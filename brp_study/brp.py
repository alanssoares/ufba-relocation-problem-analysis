"""Model and solvers for the restricted, unique, deterministic, static BRP.

Conventions
-----------
* Containers are labelled 1..N; the label is the retrieval order (1 leaves first).
* Stacks are stored bottom -> top. Public move tuples are 1-based: (src, dst).
* Retrievals are free and automatic: whenever the current target (smallest
  remaining label) is on top of its stack it leaves immediately.
* Restricted variant: the only containers that may be relocated are the ones
  above the current target, and they must come from the target's stack.
* Every relocation costs 1 reshuffle. Stack height never exceeds H.
"""

from __future__ import annotations

import heapq
import itertools
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

Move = tuple[int, int]  # (src, dst), 1-based stack numbers


# ---------------------------------------------------------------------------
# Instances
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Instance:
    file: str
    inst_id: int
    W: int
    H: int
    N: int
    stacks: tuple[tuple[int, ...], ...]  # bottom -> top


def load_instances(path: str | Path) -> list[Instance]:
    """Load all instances of one BRP JSON file (format described in data/instances/LEIAME.md)."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    meta = data["metadata"]
    W, H, N = meta["W"], meta["H"], meta["N"]
    out = []
    for item in data["instancias"]:
        stacks = tuple(tuple(s) for s in item["stacks"])
        if len(stacks) != W:
            raise ValueError(f"{path.name} id={item['id']}: expected {W} stacks, got {len(stacks)}")
        if sorted(c for s in stacks for c in s) != list(range(1, N + 1)):
            raise ValueError(f"{path.name} id={item['id']}: labels are not a permutation of 1..{N}")
        if any(len(s) > H for s in stacks):
            raise ValueError(f"{path.name} id={item['id']}: initial stack exceeds H={H}")
        out.append(Instance(path.name, item["id"], W, H, N, stacks))
    return out


# ---------------------------------------------------------------------------
# Shared mechanics
# ---------------------------------------------------------------------------

def _stabilize(stacks: list[list[int]]) -> None:
    """Retrieve, in order, every target that is on top of its stack (in place)."""
    while True:
        t = min((c for s in stacks for c in s), default=None)
        if t is None:
            return
        for s in stacks:
            if s and s[-1] == t:
                s.pop()
                break
        else:
            return


def _locate(stacks: list[list[int]], label: int) -> int:
    for i, s in enumerate(stacks):
        if label in s:
            return i
    raise KeyError(label)


def verify(inst: Instance, moves: list[Move]) -> tuple[bool, str]:
    """Independent feasibility check of a relocation sequence.

    Replays the moves from the initial layout and checks, for each relocation:
    the source is the target's stack, the source is not empty, the destination
    is a different stack with height < H. At the end the yard must be empty.
    """
    stacks = [list(s) for s in inst.stacks]
    _stabilize(stacks)
    for k, (src, dst) in enumerate(moves, start=1):
        if not (1 <= src <= inst.W and 1 <= dst <= inst.W):
            return False, f"move {k}: stack number out of range"
        if src == dst:
            return False, f"move {k}: source equals destination"
        s, d = src - 1, dst - 1
        if not stacks[s]:
            return False, f"move {k}: source stack is empty"
        target = min(c for st in stacks for c in st)
        if target not in stacks[s]:
            return False, f"move {k}: source stack does not hold the current target {target}"
        if len(stacks[d]) >= inst.H:
            return False, f"move {k}: destination stack is full (H={inst.H})"
        stacks[d].append(stacks[s].pop())
        _stabilize(stacks)
    if any(stacks):
        return False, "yard not empty at the end"
    return True, "ok"


def _simulate_detailed(inst: Instance, moves: list[Move]) -> list[tuple[int, int, int]] | None:
    """Replay moves and return (container, src, dst) per move, or None if infeasible."""
    stacks = [list(s) for s in inst.stacks]
    _stabilize(stacks)
    detail = []
    for src, dst in moves:
        s, d = src - 1, dst - 1
        if not (0 <= s < inst.W and 0 <= d < inst.W) or s == d or not stacks[s]:
            return None
        target = min(c for st in stacks for c in st)
        if target not in stacks[s] or len(stacks[d]) >= inst.H:
            return None
        c = stacks[s].pop()
        stacks[d].append(c)
        detail.append((c, src, dst))
        _stabilize(stacks)
    return detail if not any(stacks) else None


def condense(inst: Instance, moves: list[Move]) -> list[Move]:
    """Solution condensation (Jin et al., 2015, Sec. 4.3.5).

    Two consecutive relocations of the same container c, s1->s2 then s2->s3,
    are merged into s1->s3 when no container leaves or enters s3 in between.
    The paper's three conditions are checked, and every merge is also accepted
    only if the whole solution still verifies (a safety net for the restricted
    variant, where retrievals also change stack tops).
    """
    moves = list(moves)
    improved = True
    while improved:
        improved = False
        detail = _simulate_detailed(inst, moves)
        if detail is None:
            return moves
        last_move_of: dict[int, int] = {}
        for j, (c, s2_src, s3_dst) in enumerate(detail):
            i = last_move_of.get(c)
            last_move_of[c] = j
            if i is None:
                continue
            _, s1, s2 = detail[i]
            if s2 != s2_src:  # c must be moved again from where it was put
                continue
            s3 = s3_dst
            between = detail[i + 1:j]
            if any(src == s3 for _, src, _ in between) or any(dst == s3 for _, _, dst in between):
                continue
            candidate = list(moves)
            candidate[i] = (s1, s3)
            del candidate[j]
            if len(candidate) < len(moves) and verify(inst, candidate)[0]:
                moves = candidate
                improved = True
                break
    return moves


def badly_placed(stacks) -> int:
    """Admissible lower bound: containers with a smaller label somewhere below them.

    Each such container must be relocated at least once (Jin et al. use the same
    count as the first term of their lower bound).
    """
    count = 0
    for s in stacks:
        running_min = None
        for c in s:
            if running_min is not None and running_min < c:
                count += 1
            running_min = c if running_min is None else min(running_min, c)
    return count


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class SolveResult:
    method: str
    moves: list[Move] | None
    status: str                      # 'optimal', 'feasible', 'timeout'
    time_s: float
    lower_bound: int | None = None   # valid LB on the optimum when known
    nodes: int | None = None         # expanded states (A*) or tree nodes (GLAH)
    extra: dict = field(default_factory=dict)

    @property
    def reshuffles(self) -> int | None:
        return None if self.moves is None else len(self.moves)


# ---------------------------------------------------------------------------
# Min-Max (Caserta, Voss & Sniedovich, 2012) -- constructive baseline
# ---------------------------------------------------------------------------

def minmax_destination(stacks: list[list[int]], src: int, r: int, N: int, H: int) -> int:
    """Min-Max rule for the blocker r on top of stack `src` (0-based result).

    D = stacks other than src with height < H. min(i) = smallest label in stack i
    (N+1 if empty). If some i in D has min(i) > r, take the one with the smallest
    min(i); otherwise take the one with the largest min(i). Ties: lowest index.
    """
    cand = [i for i in range(len(stacks)) if i != src and len(stacks[i]) < H]
    if not cand:
        raise RuntimeError("no destination with free space")
    mins = {i: (min(stacks[i]) if stacks[i] else N + 1) for i in cand}
    ok = [i for i in cand if mins[i] > r]
    if ok:
        return min(ok, key=lambda i: (mins[i], i))
    return max(cand, key=lambda i: (mins[i], -i))


def solve_minmax(inst: Instance) -> SolveResult:
    t0 = time.perf_counter()
    stacks = [list(s) for s in inst.stacks]
    _stabilize(stacks)
    moves: list[Move] = []
    while any(stacks):
        target = min(c for s in stacks for c in s)
        src = _locate(stacks, target)
        r = stacks[src][-1]
        dst = minmax_destination(stacks, src, r, inst.N, inst.H)
        stacks[dst].append(stacks[src].pop())
        moves.append((src + 1, dst + 1))
        _stabilize(stacks)
    return SolveResult("Min-Max", moves, "feasible", time.perf_counter() - t0)


# ---------------------------------------------------------------------------
# A* (exact) -- state-space search with h = number of badly placed containers
# ---------------------------------------------------------------------------

def _successor_states(state, H):
    """Yield (next_state, move) for the only legal relocations from `state`.

    `state` is stabilized, so the target is never on top; the blocker is the top
    of the target's stack and may go to any other stack with free space.
    """
    target = min(c for s in state for c in s)
    src = next(i for i, s in enumerate(state) if target in s)
    r = state[src][-1]
    for dst in range(len(state)):
        if dst == src or len(state[dst]) >= H:
            continue
        work = [list(s) for s in state]
        work[src].pop()
        work[dst].append(r)
        _stabilize(work)
        yield tuple(tuple(s) for s in work), (src + 1, dst + 1)


def solve_astar(inst: Instance, time_limit: float = 60.0) -> SolveResult:
    """Exact A* with f = g + h, unit step cost, duplicate detection with reopening.

    Stops at `time_limit` seconds. In that case the result is 'timeout' and the
    smallest f in the open list (the f of the node being popped) is returned as a
    lower bound on the optimum.
    """
    t0 = time.perf_counter()
    start_stacks = [list(s) for s in inst.stacks]
    _stabilize(start_stacks)
    start = tuple(tuple(s) for s in start_stacks)

    counter = itertools.count()
    open_heap = [(badly_placed(start), 0, next(counter), start)]
    best_g = {start: 0}
    parent: dict = {}
    expanded = 0

    while open_heap:
        f, neg_g, _, state = heapq.heappop(open_heap)
        g = -neg_g
        if g > best_g.get(state, float("inf")):
            continue  # stale entry
        if not any(state):
            moves = []
            node = state
            while node in parent:
                node, mv = parent[node]
                moves.append(mv)
            moves.reverse()
            return SolveResult("A*", moves, "optimal", time.perf_counter() - t0,
                               lower_bound=len(moves), nodes=expanded)
        if time.perf_counter() - t0 > time_limit:
            return SolveResult("A*", None, "timeout", time.perf_counter() - t0,
                               lower_bound=f, nodes=expanded)
        expanded += 1
        for nxt, mv in _successor_states(state, inst.H):
            ng = g + 1
            if ng < best_g.get(nxt, float("inf")):
                best_g[nxt] = ng
                parent[nxt] = (state, mv)
                heapq.heappush(open_heap, (ng + badly_placed(nxt), -ng, next(counter), nxt))

    raise RuntimeError("A* exhausted the state space without reaching an empty yard")


# ---------------------------------------------------------------------------
# Greedy look-ahead heuristic, restricted variant (Jin, Zhu & Lim, 2015, adapted)
# ---------------------------------------------------------------------------

class _GLAHContext:
    """Holds the incumbent solution and the parameters shared by all levels."""

    def __init__(self, inst: Instance, depth: int, n_ftbg: int, n_ftbb: int, deadline: float):
        self.inst = inst
        self.depth = depth
        self.n_ftbg = n_ftbg
        self.n_ftbb = n_ftbb
        self.deadline = deadline
        self.best: list[Move] | None = None
        self.nodes = 0
        self.timed_out = False

    def offer(self, moves: list[Move]) -> None:
        """Condense and verify a complete solution, keep it if it is the best so far."""
        moves = condense(self.inst, moves)
        if (self.best is None or len(moves) < len(self.best)) and verify(self.inst, moves)[0]:
            self.best = moves


def _bottom_level_move(stacks: list[list[int]], N: int, H: int) -> tuple[int, int]:
    """Evaluation heuristic for one relocation (paper Sec. 4.3.2, Cases 1, 3, 4).

    Case 2 (vacating a space by moving a non-blocker) and gap utilisation are not
    available in the restricted variant, because they move containers that are
    not above the target.
    """
    target = min(c for s in stacks for c in s)
    src = _locate(stacks, target)
    r = stacks[src][-1]
    cand = [i for i in range(len(stacks)) if i != src and len(stacks[i]) < H]
    if not cand:
        raise RuntimeError("no destination with free space")
    mins = {i: (min(stacks[i]) if stacks[i] else N + 1) for i in cand}

    # Case 1: a stack that can support r (its minimum is above r).
    supporting = [i for i in cand if mins[i] > r]
    if supporting:
        return src, min(supporting, key=lambda i: (mins[i], i))

    # Cases 3 and 4: stack with the largest minimum, with the special check.
    s_best = max(cand, key=lambda i: (mins[i], -i))
    above_target = stacks[src][stacks[src].index(target) + 1:]
    if len(stacks[s_best]) == H - 1 and r != min(above_target) and len(cand) > 1:
        rest = [i for i in cand if i != s_best]
        s_best = max(rest, key=lambda i: (mins[i], -i))
    return src, s_best


def _evaluate(inst: Instance, stacks: list[list[int]]) -> list[Move]:
    """Bottom level: complete a layout with the evaluation heuristic (1-based moves)."""
    work = [list(s) for s in stacks]
    _stabilize(work)
    moves: list[Move] = []
    while any(work):
        src, dst = _bottom_level_move(work, inst.N, inst.H)
        work[dst].append(work[src].pop())
        moves.append((src + 1, dst + 1))
        _stabilize(work)
    return moves


def _candidate_destinations(stacks: list[list[int]], N: int, H: int,
                            n_ftbg: int, n_ftbb: int, advised_dst: int) -> list[int]:
    """Middle level: the reloList of Sec. 4.2.2, restricted to the blocker on top.

    Destinations are split into FT-BG (the blocker becomes well placed there) and
    FT-BB (it stays badly placed). FT-BG is sorted by the gap min(s2) - g(c) in
    ascending order, FT-BB by g(c) - min(s2) in ascending order. The evaluation
    heuristic's own choice is appended (the "outer-sync" fix of Sec. 4.3.4).
    """
    target = min(c for s in stacks for c in s)
    src = _locate(stacks, target)
    r = stacks[src][-1]
    cand = [i for i in range(len(stacks)) if i != src and len(stacks[i]) < H]
    mins = {i: (min(stacks[i]) if stacks[i] else N + 1) for i in cand}
    bg = sorted((i for i in cand if mins[i] > r), key=lambda i: (mins[i] - r, i))[:n_ftbg]
    bb = sorted((i for i in cand if mins[i] < r), key=lambda i: (r - mins[i], i))[:n_ftbb]
    out = bg + bb
    if advised_dst not in out:
        out.append(advised_dst)
    return out


def _tree_search(ctx: _GLAHContext, stacks: list[list[int]], path: list[Move],
                 prefix: list[Move]) -> tuple[float, Move | None]:
    """Look-ahead tree search. Returns (cost, first move of the best branch)."""
    inst = ctx.inst
    ctx.nodes += 1
    d = len(path)
    best_len = len(ctx.best) if ctx.best is not None else float("inf")
    if len(prefix) + d + badly_placed(stacks) >= best_len:
        return float("inf"), None  # pruned by the lower bound (paper line 3)
    if time.perf_counter() > ctx.deadline:
        ctx.timed_out = True
        return float("inf"), None

    if not any(stacks) or d == ctx.depth:
        evaluated = _evaluate(inst, stacks)
        ctx.offer(prefix + path + evaluated)
        return d + len(evaluated), None

    target = min(c for s in stacks for c in s)
    src = _locate(stacks, target)
    eval_src, eval_dst = _bottom_level_move(stacks, inst.N, inst.H)
    dsts = _candidate_destinations(stacks, inst.N, inst.H, ctx.n_ftbg, ctx.n_ftbb, eval_dst)

    best_cost, best_move = float("inf"), None
    for dst in dsts:
        child = [list(s) for s in stacks]
        child[dst].append(child[src].pop())
        _stabilize(child)
        cost, _ = _tree_search(ctx, child, path + [(src + 1, dst + 1)], prefix)
        if cost < best_cost:
            best_cost, best_move = cost, (src + 1, dst + 1)
    return best_cost, best_move


def solve_glah(inst: Instance, depth: int = 3, n_ftbg: int = 5, n_ftbb: int = 3,
               time_limit: float = 60.0) -> SolveResult:
    """Greedy look-ahead heuristic for the restricted BRP.

    Top level: greedy mechanism. Each stage asks the look-ahead for one relocation,
    applies it, retrieves what is free, and stops early if the lower bound
    cannot beat the incumbent. Middle level: tree search of depth `depth` over
    destinations. Bottom level: evaluation heuristic (Min-Max with the paper's
    Case 3 check). Every complete solution is condensed and verified.
    """
    t0 = time.perf_counter()
    deadline = t0 + time_limit
    ctx = _GLAHContext(inst, depth, n_ftbg, n_ftbb, deadline)

    stacks = [list(s) for s in inst.stacks]
    _stabilize(stacks)
    ctx.offer(_evaluate(inst, stacks))  # incumbent from the evaluation heuristic

    sol: list[Move] = []
    while any(stacks):
        if len(sol) + badly_placed(stacks) >= len(ctx.best):
            break
        if time.perf_counter() > deadline:
            ctx.timed_out = True
            break
        _, advice = _tree_search(ctx, stacks, [], sol)
        if advice is None:  # all branches pruned or out of time: follow the evaluation
            advice = _bottom_level_move(stacks, inst.N, inst.H)
            advice = (advice[0] + 1, advice[1] + 1)
        src, dst = advice[0] - 1, advice[1] - 1
        stacks[dst].append(stacks[src].pop())
        _stabilize(stacks)
        sol.append(advice)

    if not any(stacks):
        ctx.offer(sol)

    status = "timeout" if ctx.timed_out else "feasible"
    return SolveResult(f"GLAH-R (D={depth})", ctx.best, status, time.perf_counter() - t0,
                       nodes=ctx.nodes, extra={"depth": depth})


# ---------------------------------------------------------------------------
# Reference: breadth-first search (used in tests to cross-check A*)
# ---------------------------------------------------------------------------

def solve_bfs(inst: Instance) -> int:
    """Optimal number of reshuffles by breadth-first search over the same state graph."""
    start_stacks = [list(s) for s in inst.stacks]
    _stabilize(start_stacks)
    start = tuple(tuple(s) for s in start_stacks)
    frontier = {start}
    seen = {start}
    steps = 0
    while True:
        if any(not any(state) for state in frontier):  # some state has an empty yard
            return steps
        nxt = set()
        for state in frontier:
            for ns, _ in _successor_states(state, inst.H):
                if ns not in seen:
                    seen.add(ns)
                    nxt.add(ns)
        frontier = nxt
        steps += 1
