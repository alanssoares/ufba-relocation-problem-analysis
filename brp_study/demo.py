"""Helpers for live demos (Google Colab notebook in notebooks/brp_demo.ipynb).

    from demo import get_instance, render, solve_all, table_md, replay
    inst = get_instance("brp_W3_H4_N8.json", 8)
    print(render(inst.stacks, inst.H))
    rows = solve_all(inst, time_limit=10)
    print(table_md(rows))
    print(replay(inst, rows[0]["moves"], restricted=True))
"""

from __future__ import annotations

import time
from pathlib import Path

from brp import (Instance, Move, load_instances, verify, solve_minmax, solve_astar, solve_glah,
                 _stabilize)
from brp_unrestricted import solve_astar_u, solve_glah_u

DATA = Path(__file__).resolve().parent.parent / "data" / "instances"


def list_files() -> list[str]:
    """Names of the instance files shipped with the repository."""
    return sorted(p.name for p in DATA.glob("brp_*.json"))


def get_instance(file: str, inst_id: int) -> Instance:
    """One instance of a data file, by its id (1 to 10)."""
    for inst in load_instances(DATA / file):
        if inst.inst_id == inst_id:
            return inst
    raise KeyError(f"{file} has no instance with id={inst_id}")


def instance_from_stacks(stacks: list[list[int]], H: int) -> Instance:
    """Build an instance from a list of stacks (bottom -> top), e.g. typed in class.

    Labels must be 1..N without repetitions, and no stack may exceed H.
    """
    N = sum(len(s) for s in stacks)
    if sorted(c for s in stacks for c in s) != list(range(1, N + 1)):
        raise ValueError(f"labels must be a permutation of 1..{N}")
    if any(len(s) > H for s in stacks):
        raise ValueError(f"a stack exceeds H={H}")
    return Instance("custom", 0, len(stacks), H, N, tuple(tuple(s) for s in stacks))


def render(stacks, H: int) -> str:
    """ASCII drawing of the yard, bottom at the bottom, same style as LEIAME.md.

    Only the occupied levels are drawn; H is used for the caption."""
    W = len(stacks)
    width = max([2] + [len(str(c)) for s in stacks for c in s])
    cell = lambda x: str(x).rjust(width)  # noqa: E731
    lines = []
    top = max([1] + [len(s) for s in stacks])  # empty rows at the top are not drawn
    for level in range(top - 1, -1, -1):
        row = [cell(s[level]) if level < len(s) else " " * width for s in stacks]
        lines.append("  ".join(row).rstrip())
    lines.append("  ".join("-" * width for _ in range(W)))
    lines.append("  ".join(f"P{i + 1}".rjust(width) for i in range(W)) + f"   (H = {H})")
    return "\n".join(lines)


def replay(inst: Instance, moves: list[Move], restricted: bool = True, show_yard: bool = True) -> str:
    """Step-by-step replay of a solution: each relocation, what leaves, and the yard."""
    ok, msg = verify(inst, moves, restricted=restricted)
    out = [f"Variante: {'restrita' if restricted else 'irrestrita'} | movimentos: {len(moves)} | "
           f"verificação: {'OK' if ok else 'FALHOU - ' + msg}", ""]
    stacks = [list(s) for s in inst.stacks]
    out.append("Configuração inicial:")
    out.append(render(stacks, inst.H))
    before = {c for s in stacks for c in s}
    _stabilize(stacks)
    gone = sorted(before - {c for s in stacks for c in s})
    if gone:
        out.append(f"Retirados de imediato: {gone}")
    for k, (src, dst) in enumerate(moves, start=1):
        if not stacks[src - 1]:
            out.append(f"{k}. P{src} -> P{dst}: origem vazia, parando.")
            break
        target = min((c for s in stacks for c in s), default=None)
        c = stacks[src - 1].pop()
        stacks[dst - 1].append(c)
        kind = "bloqueia o alvo" if target in stacks[src - 1] else "antecipada"
        before = {x for s in stacks for x in s}
        _stabilize(stacks)
        gone = sorted(before - {x for s in stacks for x in s})
        out.append("")
        out.append(f"{k}. contêiner {c}: P{src} -> P{dst} ({kind})"
                   + (f" | saem: {gone}" if gone else ""))
        if show_yard and any(stacks):
            out.append(render(stacks, inst.H))
    out.append("")
    out.append("Pátio vazio." if not any(stacks) else "Pátio NÃO ficou vazio.")
    return "\n".join(out)


def solve_all(inst: Instance, time_limit: float = 10.0, depths=(3, 4),
              variants=("restricted", "unrestricted")) -> list[dict]:
    """Run every method of the study on one instance and verify each solution.

    Restricted: Min-Max, A*, GLAH-R (D in depths).
    Unrestricted: GLAH-U (D in depths), then A*-U seeded with the best
    unrestricted-feasible heuristic solution found (Min-Max included).
    """
    rows = []

    def add(variant, res, restricted):
        ok = res.moves is not None and verify(inst, res.moves, restricted=restricted)[0]
        rows.append({"variant": variant, "method": res.method, "status": res.status,
                     "reshuffles": res.reshuffles if ok else None, "verified": ok,
                     "time_s": res.time_s, "lower_bound": res.lower_bound, "moves": res.moves})

    if "restricted" in variants:
        add("restrita", solve_minmax(inst), True)
        add("restrita", solve_astar(inst, time_limit=time_limit), True)
        for d in depths:
            add("restrita", solve_glah(inst, depth=d, time_limit=time_limit), True)
    if "unrestricted" in variants:
        heur = [solve_minmax(inst)] + [solve_glah_u(inst, depth=d, time_limit=time_limit) for d in depths]
        for r in heur[1:]:
            add("irrestrita", r, False)
        incumbent = min((r.moves for r in heur if r.moves is not None), key=len)
        astar = solve_astar_u(inst, time_limit=time_limit, incumbent=incumbent)
        if astar.status != "optimal":
            astar.moves = None  # only proved optima are reported for the exact method
        add("irrestrita", astar, False)
    return rows


def table_md(rows: list[dict]) -> str:
    """Markdown table of solve_all() rows."""
    lines = ["| Variante | Método | Reshuffles | Status | Verificada | Tempo (s) | Limite inferior |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['variant']} | {r['method']} | {'-' if r['reshuffles'] is None else r['reshuffles']} | "
                     f"{r['status']} | {'sim' if r['verified'] else 'não'} | {r['time_s']:.3f} | "
                     f"{'-' if r['lower_bound'] is None else r['lower_bound']} |")
    return "\n".join(lines)


def find(rows: list[dict], method: str) -> dict:
    """The solve_all() row of a method, by name (e.g. 'A*', 'GLAH-U (D=3)')."""
    for r in rows:
        if r["method"] == method:
            return r
    raise KeyError(f"no method {method!r}; available: {[r['method'] for r in rows]}")


if __name__ == "__main__":
    t0 = time.perf_counter()
    inst = get_instance("brp_W3_H4_N8.json", 8)
    rows = solve_all(inst, time_limit=10)
    print(table_md(rows))
    print()
    print(replay(inst, find(rows, "A*-U")["moves"], restricted=False))
    print(f"\n({time.perf_counter() - t0:.2f}s)")
