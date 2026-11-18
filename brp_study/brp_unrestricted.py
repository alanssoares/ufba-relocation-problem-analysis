"""Unrestricted BRP (U-CRP): exact search and the full greedy look-ahead heuristic.

Variant
-------
Same conventions as ``brp.py`` (labels = retrieval order, stacks bottom -> top,
1-based public moves, automatic free retrievals, height limit H, 1 reshuffle per
relocation), except that **any top container of any stack may be relocated** to
any other stack with free space. Every restricted solution is also an
unrestricted one, so the unrestricted optimum is never larger.

Contents
--------
* ``lower_bound_u``: lower bound of Jin, Zhu & Lim (2015), Sec. 4.1.1
  (badly placed containers + the binary term k_non-BG).
* ``solve_bfs_u``: plain breadth-first search (test reference only).
* ``solve_astar_u``: exact A* with symmetry reduction, two dominance rules and
  an optional incumbent (upper bound) used for pruning.
* ``solve_glah_u``: the greedy look-ahead heuristic (GLAH) of Jin, Zhu & Lim
  (2015) as published: six relocation categories in the look-ahead, Cases 1-4
  and gap utilisation in the evaluation heuristic, outer-sync fix and
  solution condensation.
"""

from __future__ import annotations

import heapq
import itertools
import time

from brp import Instance, Move, SolveResult, badly_placed, verify

# Number of children taken from each relocation category (paper, Sec. 5).
PAPER_LIMITS = {"FT-BG": 5, "NF-BG": 5, "FT-BB": 3, "NF-BB": 3, "GG": 1, "GB": 1}
CATEGORY_ORDER = ("FT-BG", "NF-BG", "FT-BB", "NF-BB", "GG", "GB")


def _stabilize(stacks: list[list[int]]) -> None:
    """Retrieve, in order, every target that is on top of its stack (in place).

    Same behaviour as ``brp._stabilize``; the minimum is computed with
    ``map(min, ...)`` because this function dominates the running time here.
    """
    while True:
        nonempty = [s for s in stacks if s]
        if not nonempty:
            return
        t = min(map(min, nonempty))
        for s in nonempty:
            if s[-1] == t:
                s.pop()
                break
        else:
            return


def _retrieve(stacks: list[list[int]], order: list[int], k: int) -> int:
    """Faster _stabilize when the retrieval order is known.

    order: all labels of the layout in increasing order; k: index of the current
    target in it. Retrieves while the target is on top and returns the new k.
    """
    n = len(order)
    while k < n:
        t = order[k]
        for s in stacks:
            if s and s[-1] == t:
                s.pop()
                k += 1
                break
        else:
            break
    return k


# ---------------------------------------------------------------------------
# Notation of the paper (Sec. 2). An empty stack has gmin = N + 1.
# ---------------------------------------------------------------------------

def _gmin(stack, N: int) -> int:
    """Smallest label in the stack (N+1 if empty)."""
    return min(stack) if stack else N + 1


def _f(stack, N: int) -> int:
    """Smallest label in the stack except its top (N+1 if the stack has < 2 containers)."""
    return min(stack[:-1]) if len(stack) > 1 else N + 1


def lower_bound_u(stacks) -> int:
    """Lower bound of Sec. 4.1.1 (Forster & Bortfeldt, 2012b), valid for the U-CRP.

    LB = (badly placed containers) + k_non-BG, where k_non-BG = 1 iff there is no
    empty stack and min_s gtop(s) > max_s gmin(s). In that situation every top is
    badly placed and every destination already holds a smaller label, so the
    first relocation leaves the moved container badly placed again and it needs
    at least one more move.
    """
    if not any(stacks):
        return 0
    lb = badly_placed(stacks)
    if all(stacks) and min(s[-1] for s in stacks) > max(min(s) for s in stacks):
        lb += 1
    return lb


# ---------------------------------------------------------------------------
# Replay and condensation on an arbitrary start layout (unrestricted rules)
# ---------------------------------------------------------------------------

def _replay_u(start, moves: list[Move], H: int) -> list[tuple[int, int, int]] | None:
    """Replay 1-based moves from `start`; return (container, src, dst) per move,
    or None if a move is illegal or the yard is not empty at the end."""
    stacks = [list(s) for s in start]
    W = len(stacks)
    order = sorted(c for s in stacks for c in s)
    k = _retrieve(stacks, order, 0)
    detail = []
    for src, dst in moves:
        s, d = src - 1, dst - 1
        if not (0 <= s < W and 0 <= d < W) or s == d or not stacks[s] or len(stacks[d]) >= H:
            return None
        c = stacks[s].pop()
        stacks[d].append(c)
        detail.append((c, src, dst))
        k = _retrieve(stacks, order, k)
    return detail if k == len(order) else None


def condense_u(start, moves: list[Move], H: int) -> list[Move]:
    """Solution condensation (Sec. 4.3.5) for the unrestricted variant.

    For two consecutive relocations of the same container c, <c: s1->s2> and then
    <c: s2->s3>, with no container moved out of or into s3 in between, the first
    becomes <c: s1->s3> and the second is removed. Pairs with s3 == s1 are left
    alone (the merged move would be s1->s1). Each merge is kept only if the whole
    sequence still replays to an empty yard, which also covers retrievals.
    """
    moves = list(moves)
    while True:
        detail = _replay_u(start, moves, H)
        if detail is None:
            return moves
        merged = False
        last_move_of: dict[int, int] = {}
        for j, (c, a, b) in enumerate(detail):
            i = last_move_of.get(c)
            last_move_of[c] = j
            if i is None:
                continue
            _, s1, s2 = detail[i]
            s3 = b
            if s2 != a or s3 == s1:
                continue
            if any(x == s3 or y == s3 for _, x, y in detail[i + 1:j]):
                continue
            candidate = moves[:i] + [(s1, s3)] + moves[i + 1:j] + moves[j + 1:]
            if _replay_u(start, candidate, H) is not None:
                moves = candidate
                merged = True
                break
        if not merged:
            return moves


# ---------------------------------------------------------------------------
# Successor generation for the exact methods
# ---------------------------------------------------------------------------

def _successors_u(state, H: int, one_empty: bool = False, skip_container: int | None = None):
    """Yield (next_state, move, moved_container, retrieved_any) for every relocation.

    one_empty: only the first empty destination is generated (the others give a
    permutation of the same layout). skip_container: do not move this label
    (dominance rule used by A*).
    """
    W = len(state)
    n_before = sum(len(s) for s in state)
    for s1 in range(W):
        src = state[s1]
        if not src:
            continue
        c = src[-1]
        if c == skip_container:
            continue
        empty_seen = False
        for s2 in range(W):
            if s2 == s1 or len(state[s2]) >= H:
                continue
            if one_empty and not state[s2]:
                if empty_seen:
                    continue
                empty_seen = True
            work = [list(s) for s in state]
            work[s1].pop()
            work[s2].append(c)
            _stabilize(work)
            retrieved = sum(len(s) for s in work) < n_before
            yield tuple(tuple(s) for s in work), (s1 + 1, s2 + 1), c, retrieved


def _start_state(inst: Instance):
    stacks = [list(s) for s in inst.stacks]
    _stabilize(stacks)
    return tuple(tuple(s) for s in stacks)


def solve_bfs_u(inst: Instance) -> int:
    """Optimal number of reshuffles of the U-CRP by plain breadth-first search.

    No symmetry reduction and no dominance rule: it is the independent reference
    used by the tests to check A*.
    """
    start = _start_state(inst)
    frontier, seen, steps = {start}, {start}, 0
    while True:
        if any(not any(state) for state in frontier):
            return steps
        nxt = set()
        for state in frontier:
            for ns, _, _, _ in _successors_u(state, inst.H):
                if ns not in seen:
                    seen.add(ns)
                    nxt.add(ns)
        if not nxt:
            raise RuntimeError("BFS exhausted the state space without reaching an empty yard")
        frontier = nxt
        steps += 1


# ---------------------------------------------------------------------------
# A* (exact) for the U-CRP
# ---------------------------------------------------------------------------

def solve_astar_u(inst: Instance, time_limit: float = 60.0,
                  incumbent: list[Move] | None = None,
                  max_nodes: int = 3_000_000) -> SolveResult:
    """Exact A* for the U-CRP with f = g + lower_bound_u.

    Reductions (all preserve optimality, checked against BFS in the tests):
    * Symmetry: layouts that are permutations of each other share one entry in
      the closed table, and only the first empty stack is used as destination.
    * Dominance: the container moved last is not moved again unless a retrieval
      happened in between (c: s1->s2, c: s2->s3 is never shorter than c: s1->s3).
    * Incumbent: with an incumbent of length UB, nodes with f >= UB are dropped.
      If the open list empties (or its best f reaches UB) the incumbent is optimal.

    Stops after `time_limit` seconds or `max_nodes` generated nodes (memory
    guard); then the result is 'timeout' with the incumbent (if any) as the
    solution and the smallest open f as lower bound.
    """
    t0 = time.perf_counter()
    start = _start_state(inst)
    ub = len(incumbent) if incumbent is not None else float("inf")

    def result(moves, status, lb, expanded, reason=""):
        extra = {"reason": reason} if reason else {}
        return SolveResult("A*-U", moves, status, time.perf_counter() - t0,
                           lower_bound=lb, nodes=expanded, extra=extra)

    if not any(start):
        return result([], "optimal", 0, 0)
    h0 = lower_bound_u(start)
    if h0 >= ub:
        return result(list(incumbent), "optimal", ub, 0)

    canon = lambda s: tuple(sorted(s))  # noqa: E731
    counter = itertools.count()
    node_parent = [-1]
    node_move: list[Move | None] = [None]
    best_g = {canon(start): 0}
    open_heap = [(h0, 0, next(counter), 0, start, None)]
    expanded = 0

    while open_heap:
        f, neg_g, _, nid, state, skip = heapq.heappop(open_heap)
        g = -neg_g
        if g > best_g.get(canon(state), float("inf")):
            continue  # stale entry
        if f >= ub:
            break  # every remaining node has f >= UB: the incumbent is optimal
        if not any(state):
            moves = []
            while nid > 0:
                moves.append(node_move[nid])
                nid = node_parent[nid]
            moves.reverse()
            return result(moves, "optimal", len(moves), expanded)
        if time.perf_counter() - t0 > time_limit:
            return result(None if incumbent is None else list(incumbent), "timeout",
                          min(f, ub), expanded, "time")
        if len(node_parent) > max_nodes:
            return result(None if incumbent is None else list(incumbent), "timeout",
                          min(f, ub), expanded, "memory")
        expanded += 1
        for nxt, mv, c, retrieved in _successors_u(state, inst.H, one_empty=True, skip_container=skip):
            ng = g + 1
            key = canon(nxt)
            if ng >= best_g.get(key, float("inf")):
                continue
            nf = ng + lower_bound_u(nxt)
            if nf >= ub:
                continue
            best_g[key] = ng
            node_parent.append(nid)
            node_move.append(mv)
            heapq.heappush(open_heap, (nf, -ng, next(counter), len(node_parent) - 1, nxt,
                                       None if retrieved else c))

    if incumbent is not None:
        return result(list(incumbent), "optimal", ub, expanded)
    raise RuntimeError("A*-U exhausted the state space without reaching an empty yard")


# ---------------------------------------------------------------------------
# Bottom level: evaluation heuristic (Sec. 4.3, Algorithms 3 and 4)
# ---------------------------------------------------------------------------

def _apply(work: list[list[int]], moves: list[Move], a: int, b: int) -> None:
    work[b].append(work[a].pop())
    moves.append((a + 1, b + 1))


def _gap_utilize(work, moves, s1: int, s2: int, c: int, exclude: tuple[int, ...], N: int, H: int) -> None:
    """Algorithm 4. Before the X-Good relocation <c: s1->s2>, while s2 keeps at
    least two free slots, move onto s2 a badly placed top c3 of another stack s3
    with c < c3 < gmin(s2) (largest such c3). c3 is then well placed, and c will
    still be well placed on top of it."""
    W = len(work)
    while len(work[s2]) <= H - 2:
        g2 = _gmin(work[s2], N)
        best = None
        for s3 in range(W):
            if s3 == s1 or s3 == s2 or s3 in exclude:
                continue
            st = work[s3]
            if len(st) < 2:
                continue
            c3 = st[-1]
            if c3 > _f(st, N) and c < c3 < g2 and (best is None or c3 > work[best][-1]):
                best = s3
        if best is None:
            return
        _apply(work, moves, best, s2)


def _clear_target(work: list[list[int]], moves: list[Move], N: int, H: int, target: int) -> None:
    """Relocate every blocker above `target` (Sec. 4.3.2, Cases 1-4)."""
    W = len(work)
    ss = next(i for i, s in enumerate(work) if target in s)
    while work[ss][-1] != target:
        c = work[ss][-1]
        gm = [_gmin(s, N) for s in work]
        cand = [i for i in range(W) if i != ss and len(work[i]) < H]
        if not cand:
            raise RuntimeError("no destination with free space")

        # Case 1: some stack supports c -> the one with the smallest gmin.
        s1_set = [i for i in cand if gm[i] > c]
        if s1_set:
            s0 = min(s1_set, key=lambda i: (gm[i], i))
            _gap_utilize(work, moves, ss, s0, c, (), N, H)
            _apply(work, moves, ss, s0)
            continue

        # Case 2: free a good slot for c by moving a well placed top c0 of s0 to
        # an assistant stack sa that supports c0. s0 = largest gtop, sa = smallest gmin.
        best_s0, best_sa = None, None
        for s0 in range(W):
            st = work[s0]
            if s0 == ss or not st:
                continue
            c0, f0 = st[-1], _f(st, N)
            if not (c0 < f0 and c < f0):
                continue
            assistants = [a for a in range(W) if a not in (ss, s0) and len(work[a]) < H and gm[a] > c0]
            if not assistants:
                continue
            if best_s0 is None or c0 > work[best_s0][-1]:
                best_s0, best_sa = s0, min(assistants, key=lambda a: (gm[a], a))
        if best_s0 is not None:
            s0, sa = best_s0, best_sa
            c0 = work[s0][-1]
            _gap_utilize(work, moves, s0, sa, c0, (ss,), N, H)
            _apply(work, moves, s0, sa)
            _gap_utilize(work, moves, ss, s0, c, (sa,), N, H)
            _apply(work, moves, ss, s0)
            continue

        # Cases 3 and 4: stack with the largest gmin, with the special check of Case 3.
        s0 = max(cand, key=lambda i: (gm[i], -i))
        above_target = work[ss][work[ss].index(target) + 1:]
        if len(work[s0]) == H - 1 and c != min(above_target) and len(cand) > 1:
            rest = [i for i in cand if i != s0]
            s0 = max(rest, key=lambda i: (gm[i], -i))
        _apply(work, moves, ss, s0)


def evaluate_u(stacks, N: int, H: int) -> list[Move]:
    """Evaluation heuristic (Algorithm 3): clear the layout, return 1-based moves.

    With distinct labels the urgent target (Sec. 4.3.1) is simply the smallest one.
    """
    work = [list(s) for s in stacks]
    order = sorted(c for s in work for c in s)
    k = _retrieve(work, order, 0)
    moves: list[Move] = []
    while k < len(order):
        _clear_target(work, moves, N, H, order[k])
        k = _retrieve(work, order, k)
    return moves


# ---------------------------------------------------------------------------
# Middle level: relocation classification and look-ahead (Sec. 4.2)
# ---------------------------------------------------------------------------

def classify_relocations(stacks, N: int, H: int) -> dict[str, list[tuple[int, int]]]:
    """All legal relocations (0-based (s1, s2)) by category, each sorted as in Sec. 4.2.2.

    * Bad/Good at the source: c is badly/well placed in s1 (c > f(s1) or not).
    * Bad/Good at the destination: c < gmin(s2) (well placed after the move) or not.
    * FT/NF (Bad-X only): s1 is or is not the stack of the target.
    Sorting: X-BG by gmin(s2) - c ascending; X-BB by c - gmin(s2) ascending;
    GG and GB by f(s1) - gmin(s2) descending. Ties: lower (s1, s2).
    """
    W = len(stacks)
    target = min(c for s in stacks for c in s)
    ts = next(i for i, s in enumerate(stacks) if target in s)
    gm = [_gmin(s, N) for s in stacks]
    fs = [_f(s, N) for s in stacks]
    cats: dict[str, list] = {k: [] for k in CATEGORY_ORDER}
    for s1 in range(W):
        if not stacks[s1]:
            continue
        c = stacks[s1][-1]
        bad = c > fs[s1]
        for s2 in range(W):
            if s2 == s1 or len(stacks[s2]) >= H:
                continue
            good = c < gm[s2]
            if bad:
                pre = "FT" if s1 == ts else "NF"
                if good:
                    cats[pre + "-BG"].append((gm[s2] - c, s1, s2))
                else:
                    cats[pre + "-BB"].append((c - gm[s2], s1, s2))
            else:
                cats["GG" if good else "GB"].append((-(fs[s1] - gm[s2]), s1, s2))
    return {k: [(s1, s2) for _, s1, s2 in sorted(v)] for k, v in cats.items()}


def candidate_relocations(stacks, N: int, H: int, limits: dict[str, int],
                          advised: tuple[int, int] | None) -> list[tuple[int, int]]:
    """reloList: up to limits[X] relocations of each category, plus the evaluation
    heuristic's next relocation (outer-sync fix, Sec. 4.3.4), without duplicates."""
    cats = classify_relocations(stacks, N, H)
    out: list[tuple[int, int]] = []
    for k in CATEGORY_ORDER:
        for mv in cats[k][:limits.get(k, 0)]:
            if mv not in out:
                out.append(mv)
    if advised is not None and advised not in out:
        out.append(advised)
    return out


class _GLAHUContext:
    """Incumbent, parameters and the evaluation cache shared by all levels."""

    def __init__(self, inst: Instance, depth: int, limits: dict[str, int], deadline: float):
        self.inst = inst
        self.depth = depth
        self.limits = limits
        self.deadline = deadline
        self.best: list[Move] | None = None
        self.nodes = 0
        self.timed_out = False
        self._cache: dict = {}

    def evaluate(self, stacks) -> list[Move]:
        key = tuple(tuple(s) for s in stacks)
        res = self._cache.get(key)
        if res is None:
            if len(self._cache) > 200_000:
                self._cache.clear()
            res = evaluate_u(stacks, self.inst.N, self.inst.H)
            self._cache[key] = res
        return res

    def offer(self, moves: list[Move]) -> None:
        """Keep a complete solution if it is shorter than the incumbent and verifies."""
        if (self.best is None or len(moves) < len(self.best)) and \
                verify(self.inst, moves, restricted=False)[0]:
            self.best = list(moves)


def _tree_search_u(ctx: _GLAHUContext, stacks, path: list[Move], prefix: list[Move],
                   root) -> tuple[float, Move | None]:
    """Algorithm 2. Returns (cost, first move of the best branch).

    The cost of a leaf is the length of the condensed sequence path + evaluation,
    counted from the root of this look-ahead tree (Sec. 4.3.5: the condensed
    solution is the one used to score the leaf).
    """
    inst = ctx.inst
    ctx.nodes += 1
    d = len(path)
    best_len = len(ctx.best) if ctx.best is not None else float("inf")
    if len(prefix) + d + lower_bound_u(stacks) >= best_len:
        return float("inf"), None
    if time.perf_counter() > ctx.deadline:
        ctx.timed_out = True
        return float("inf"), None

    evaluated = ctx.evaluate(stacks)
    if not any(stacks) or d == ctx.depth:
        suffix = condense_u(root, path + evaluated, inst.H)
        ctx.offer(prefix + suffix)
        return len(suffix), None

    adv = (evaluated[0][0] - 1, evaluated[0][1] - 1)
    best_cost, best_move = float("inf"), None
    for s1, s2 in candidate_relocations(stacks, inst.N, inst.H, ctx.limits, adv):
        child = [list(s) for s in stacks]
        child[s2].append(child[s1].pop())
        _stabilize(child)
        mv = (s1 + 1, s2 + 1)
        cost, _ = _tree_search_u(ctx, child, path + [mv], prefix, root)
        if cost < best_cost:
            best_cost, best_move = cost, mv
    return best_cost, best_move


def solve_glah_u(inst: Instance, depth: int = 3, limits: dict[str, int] | None = None,
                 time_limit: float = 60.0, seed: list[Move] | None = None) -> SolveResult:
    """Greedy look-ahead heuristic (Algorithm 1) for the unrestricted BRP.

    The incumbent starts from the evaluation heuristic on the initial layout. At
    each stage the look-ahead (depth `depth`, children per category `limits`,
    default = paper values) advises one relocation; the greedy stops when the
    lower bound shows that the incumbent cannot be improved. Every complete
    solution is condensed and verified with the unrestricted rules.

    seed: optional extra starting incumbent (e.g. a restricted solution, which is
    always unrestricted-feasible). Not part of the paper; off by default.
    """
    t0 = time.perf_counter()
    limits = dict(PAPER_LIMITS if limits is None else limits)
    ctx = _GLAHUContext(inst, depth, limits, t0 + time_limit)

    stacks = [list(s) for s in inst.stacks]
    _stabilize(stacks)
    ctx.offer(condense_u(stacks, ctx.evaluate(stacks), inst.H))
    if seed is not None:
        ctx.offer(condense_u(stacks, seed, inst.H))

    sol: list[Move] = []
    while any(stacks):
        if len(sol) + lower_bound_u(stacks) >= len(ctx.best):
            break
        if time.perf_counter() > ctx.deadline:
            ctx.timed_out = True
            break
        root = tuple(tuple(s) for s in stacks)
        _, advice = _tree_search_u(ctx, stacks, [], sol, root)
        if advice is None:  # all branches pruned or out of time: follow the evaluation
            advice = ctx.evaluate(stacks)[0]
        s1, s2 = advice[0] - 1, advice[1] - 1
        stacks[s2].append(stacks[s1].pop())
        _stabilize(stacks)
        sol.append(advice)

    if not any(stacks):
        ctx.offer(condense_u(inst.stacks, sol, inst.H))

    name = f"GLAH-U (D={depth})" + ("+seed" if seed is not None else "")
    status = "timeout" if ctx.timed_out else "feasible"
    return SolveResult(name, ctx.best, status, time.perf_counter() - t0,
                       nodes=ctx.nodes, extra={"depth": depth})
