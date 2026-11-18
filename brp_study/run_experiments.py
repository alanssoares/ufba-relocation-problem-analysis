"""Run the common comparison protocol on the instance pack in data/instances.

Restricted variant (default, the one of data/instances/LEIAME.md):
    Min-Max (Caserta et al., 2012), A* (exact), GLAH-R with D=3 and D=4
    (Jin, Zhu & Lim, 2015, restricted adaptation).
    Output: results/results_long.csv, results/summary.md

Unrestricted variant (--variant unrestricted):
    Min-Max (also feasible here), A*-U (exact, seeded with the best heuristic
    solution as upper bound), GLAH-U with D=3 and D=4 (the paper's method).
    Output: results/unrestricted_long.csv, results/summary_unrestricted.md.
    If results_long.csv exists in the output folder, the restricted reference
    value of each instance is read from it to report the gain of the
    unrestricted variant (with --variant both it is the one just produced).

Every solution is re-verified with an independent simulator (with the rules of
its variant) before it enters the tables.

Usage (from the project root):
    python brp_study/run_experiments.py
    python brp_study/run_experiments.py --time-limit 30 --only W3_H4
    python brp_study/run_experiments.py --variant unrestricted
    python brp_study/run_experiments.py --variant both
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from brp import load_instances, verify, solve_minmax, solve_astar, solve_glah  # noqa: E402
from brp_unrestricted import solve_astar_u, solve_glah_u  # noqa: E402

FIELDS = ["file", "W", "H", "N", "id", "method", "status", "reshuffles", "verified",
          "z_star", "z_star_source", "gap_pct", "time_s", "lower_bound", "nodes", "moves"]
FIELDS_U = FIELDS[:11] + ["z_star_restricted", "z_star_restricted_source", "gain"] + FIELDS[11:]


def run_instance(inst, time_limit: float, depths: list[int]) -> list[dict]:
    results = [solve_minmax(inst), solve_astar(inst, time_limit=time_limit)]
    results += [solve_glah(inst, depth=d, time_limit=time_limit) for d in depths]

    verified = {}
    for r in results:
        verified[r.method] = r.moves is not None and verify(inst, r.moves)[0]

    solved = [r.reshuffles for r in results if r.moves is not None and verified[r.method]]
    best_known = min(solved)
    astar = results[1]
    if astar.status == "optimal":
        z_star, source = astar.reshuffles, "A* optimum"
    else:
        z_star, source = best_known, "best known"

    rows = []
    for r in results:
        ok = verified[r.method]
        gap = None
        if ok and z_star:
            gap = round(100.0 * (r.reshuffles - z_star) / z_star, 4)
        rows.append({
            "file": inst.file, "W": inst.W, "H": inst.H, "N": inst.N, "id": inst.inst_id,
            "method": r.method, "status": r.status,
            "reshuffles": r.reshuffles if ok else "",
            "verified": ok,
            "z_star": z_star, "z_star_source": source,
            "gap_pct": "" if gap is None else gap,
            "time_s": round(r.time_s, 4),
            "lower_bound": "" if r.lower_bound is None else r.lower_bound,
            "nodes": "" if r.nodes is None else r.nodes,
            "moves": json.dumps(r.moves) if r.moves is not None else "",
        })
    return rows


def run_instance_u(inst, time_limit: float, depths: list[int], restricted_ref: dict) -> list[dict]:
    """Unrestricted variant: Min-Max, A*-U, GLAH-U (D in depths)."""
    heur = [solve_minmax(inst)] + [solve_glah_u(inst, depth=d, time_limit=time_limit) for d in depths]
    ok_heur = [r for r in heur if r.moves is not None and verify(inst, r.moves, restricted=False)[0]]
    incumbent = min((r.moves for r in ok_heur), key=len)
    astar = solve_astar_u(inst, time_limit=time_limit, incumbent=incumbent)
    if astar.status != "optimal":
        astar.moves = None  # report only proved optima for the exact method, like the restricted A*
    results = [heur[0], astar] + heur[1:]

    verified = {r.method: r.moves is not None and verify(inst, r.moves, restricted=False)[0] for r in results}
    best_known = min(r.reshuffles for r in results if verified[r.method])
    if astar.status == "optimal":
        z_star, source = astar.reshuffles, "A*-U optimum"
    else:
        z_star, source = best_known, "best known"
    z_r, z_r_source = restricted_ref.get((inst.file, inst.inst_id), ("", ""))

    rows = []
    for r in results:
        ok = verified[r.method]
        gap = round(100.0 * (r.reshuffles - z_star) / z_star, 4) if ok and z_star else None
        rows.append({
            "file": inst.file, "W": inst.W, "H": inst.H, "N": inst.N, "id": inst.inst_id,
            "method": r.method, "status": r.status,
            "reshuffles": r.reshuffles if ok else "",
            "verified": ok,
            "z_star": z_star, "z_star_source": source,
            "z_star_restricted": z_r, "z_star_restricted_source": z_r_source,
            "gain": "" if z_r == "" else z_r - z_star,
            "gap_pct": "" if gap is None else gap,
            "time_s": round(r.time_s, 4),
            "lower_bound": "" if r.lower_bound is None else r.lower_bound,
            "nodes": "" if r.nodes is None else r.nodes,
            "moves": json.dumps(r.moves) if r.moves is not None else "",
        })
    return rows


def load_restricted_reference(path: Path) -> dict:
    """(file, id) -> (Z*_R, source) from a restricted results_long.csv, if present."""
    ref: dict = {}
    if not path.exists():
        return ref
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ref[(r["file"], int(r["id"]))] = (int(r["z_star"]), r["z_star_source"])
    return ref


def summarize_gain(rows: list[dict]) -> str:
    """Per-file comparison of the reference values Z*_R (restricted) and Z*_U (unrestricted)."""
    inst_rows = {}
    for r in rows:
        if r["z_star_restricted"] != "":
            inst_rows[(r["file"], r["id"])] = r
    if not inst_rows:
        return ""
    lines = ["## Gain of the unrestricted variant (reference values per instance)", "",
             "Z*_R: restricted reference (A* optimum or best known, from results_long.csv). "
             "Z*_U: unrestricted reference (A*-U optimum or best known). Gain = Z*_R - Z*_U. "
             "When both are proved optima the gain is exact.", "",
             "| File | W | H | N | Mean Z*_R | Mean Z*_U | Mean gain | Gain (%) "
             "| Instances with Z*_U < Z*_R | Both proved optimal |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    files: list[str] = []
    for k in inst_rows:
        if k[0] not in files:
            files.append(k[0])
    tot_r = tot_u = tot_better = tot_proved = tot_n = 0
    for f in files:
        rs = [r for k, r in inst_rows.items() if k[0] == f]
        zr = [r["z_star_restricted"] for r in rs]
        zu = [r["z_star"] for r in rs]
        better = sum(1 for a, b in zip(zr, zu) if b < a)
        proved = sum(1 for r in rs if r["z_star_source"] == "A*-U optimum"
                     and r["z_star_restricted_source"] == "A* optimum")
        pct = 100.0 * (sum(zr) - sum(zu)) / sum(zr) if sum(zr) else 0.0
        first = rs[0]
        lines.append(f"| {f} | {first['W']} | {first['H']} | {first['N']} | {statistics.fmean(zr):.2f} | "
                     f"{statistics.fmean(zu):.2f} | {statistics.fmean(a - b for a, b in zip(zr, zu)):.2f} | "
                     f"{pct:.1f} | {better}/{len(rs)} | {proved}/{len(rs)} |")
        tot_r += sum(zr)
        tot_u += sum(zu)
        tot_better += better
        tot_proved += proved
        tot_n += len(rs)
    pct = 100.0 * (tot_r - tot_u) / tot_r if tot_r else 0.0
    lines.append(f"| **All** | | | | {tot_r / tot_n:.2f} | {tot_u / tot_n:.2f} | {(tot_r - tot_u) / tot_n:.2f} | "
                 f"{pct:.1f} | {tot_better}/{tot_n} | {tot_proved}/{tot_n} |")
    lines.append("")
    return "\n".join(lines)


def summarize(rows: list[dict], title: str = "BRP comparison summary", exact: str = "A*") -> str:
    methods = []
    for r in rows:
        if r["method"] not in methods:
            methods.append(r["method"])

    def group(filter_fn):
        return [r for r in rows if filter_fn(r)]

    lines = [f"# {title}", ""]
    lines.append("## Overall (all instances)")
    lines.append("")
    lines.append("| Method | Instances | Verified | Mean reshuffles | Mean gap (%) | Max gap (%) | Matches Z* (gap 0) | Better than Min-Max | Worse than Min-Max | Mean time (s) | Max time (s) | Timeouts |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    mm_by_key = {(r["file"], r["id"]): r["reshuffles"] for r in rows if r["method"] == "Min-Max"}
    for m in methods:
        rs = group(lambda r, m=m: r["method"] == m)
        gaps = [r["gap_pct"] for r in rs if r["gap_pct"] != ""]
        recs = [r["reshuffles"] for r in rs if r["reshuffles"] != ""]
        times = [r["time_s"] for r in rs]
        better = sum(1 for r in rs if r["reshuffles"] != "" and mm_by_key[(r["file"], r["id"])] != "" and r["reshuffles"] < mm_by_key[(r["file"], r["id"])])
        worse = sum(1 for r in rs if r["reshuffles"] != "" and mm_by_key[(r["file"], r["id"])] != "" and r["reshuffles"] > mm_by_key[(r["file"], r["id"])])
        zero = sum(1 for g in gaps if g == 0)
        timeouts = sum(1 for r in rs if r["status"] == "timeout")
        lines.append(
            f"| {m} | {len(rs)} | {sum(1 for r in rs if r['verified'])} | "
            f"{statistics.fmean(recs):.2f} | {statistics.fmean(gaps):.2f} | {max(gaps):.2f} | "
            f"{zero} | {better} | {worse} | {statistics.fmean(times):.3f} | {max(times):.2f} | {timeouts} |"
            if recs and gaps else f"| {m} | {len(rs)} | - | - | - | - | - | - | - | - | - | {timeouts} |"
        )

    lines += ["", "## Per file (mean over the 10 instances of each file)", ""]
    lines.append(f"| File | W | H | N | Method | Mean reshuffles | Mean gap (%) | Mean time (s) | {exact} proved optimal | Timeouts |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    files = []
    for r in rows:
        if r["file"] not in files:
            files.append(r["file"])
    for f in files:
        for m in methods:
            rs = group(lambda r, f=f, m=m: r["file"] == f and r["method"] == m)
            if not rs:
                continue
            recs = [r["reshuffles"] for r in rs if r["reshuffles"] != ""]
            gaps = [r["gap_pct"] for r in rs if r["gap_pct"] != ""]
            times = [r["time_s"] for r in rs]
            proved = sum(1 for r in rs if r["method"] == exact and r["status"] == "optimal")
            timeouts = sum(1 for r in rs if r["status"] == "timeout")
            first = rs[0]
            mean_rs = f"{statistics.fmean(recs):.2f}" if recs else "-"
            mean_gap = f"{statistics.fmean(gaps):.2f}" if gaps else "-"
            lines.append(
                f"| {f} | {first['W']} | {first['H']} | {first['N']} | {m} | {mean_rs} | {mean_gap} | "
                f"{statistics.fmean(times):.3f} | {proved if m == exact else '-'} | {timeouts} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=str(HERE.parent / "data" / "instances"))
    ap.add_argument("--out-dir", default=str(HERE / "results"))
    ap.add_argument("--time-limit", type=float, default=30.0,
                    help="seconds per instance and method (same budget for every method)")
    ap.add_argument("--depths", type=int, nargs="+", default=[3, 4], help="GLAH look-ahead depths D")
    ap.add_argument("--only", default="", help="substring filter on file names, e.g. W3_H4")
    ap.add_argument("--variant", choices=["restricted", "unrestricted", "both"], default="restricted",
                    help="BRP variant to run (default: restricted, the one of LEIAME.md)")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in Path(args.data_dir).glob("brp_*.json") if args.only in p.name)
    if not files:
        sys.exit("no instance files matched")

    if args.variant in ("restricted", "both"):
        run_restricted(files, out, args)
    if args.variant in ("unrestricted", "both"):
        run_unrestricted(files, out, args)


def run_unrestricted(files: list[Path], out: Path, args) -> None:
    ref = load_restricted_reference(out / "results_long.csv")
    all_rows: list[dict] = []
    t_start = time.perf_counter()
    for path in files:
        for inst in load_instances(path):
            rows = run_instance_u(inst, args.time_limit, args.depths, ref)
            all_rows += rows
            summary = ", ".join(f"{r['method']}={r['reshuffles'] if r['reshuffles'] != '' else '-'}" for r in rows)
            print(f"[U] {path.name} id={inst.inst_id:>2}  z*_U={rows[0]['z_star']} ({rows[0]['z_star_source']})  "
                  f"z*_R={rows[0]['z_star_restricted'] or '?'}  {summary}", flush=True)

    with (out / "unrestricted_long.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS_U)
        w.writeheader()
        w.writerows(all_rows)
    text = summarize(all_rows, title="BRP comparison summary - unrestricted variant", exact="A*-U")
    text += "\n" + summarize_gain(all_rows)
    (out / "summary_unrestricted.md").write_text(text, encoding="utf-8")

    bad = [r for r in all_rows if r["reshuffles"] != "" and not r["verified"]]
    print(f"\n[U] Done in {time.perf_counter() - t_start:.1f}s. Rows: {len(all_rows)}. "
          f"Unverified solutions: {len(bad)}.")
    print(f"Wrote {out / 'unrestricted_long.csv'} and {out / 'summary_unrestricted.md'}")


def run_restricted(files: list[Path], out: Path, args) -> None:
    all_rows: list[dict] = []
    t_start = time.perf_counter()
    for path in files:
        for inst in load_instances(path):
            rows = run_instance(inst, args.time_limit, args.depths)
            all_rows += rows
            summary = ", ".join(f"{r['method']}={r['reshuffles'] if r['reshuffles'] != '' else 'FAIL'}" for r in rows)
            print(f"{path.name} id={inst.inst_id:>2}  z*={rows[0]['z_star']} ({rows[0]['z_star_source']})  {summary}",
                  flush=True)

    with (out / "results_long.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    (out / "summary.md").write_text(summarize(all_rows), encoding="utf-8")

    bad = [r for r in all_rows if r["reshuffles"] != "" and not r["verified"]]
    print(f"\nDone in {time.perf_counter() - t_start:.1f}s. Rows: {len(all_rows)}. "
          f"Unverified solutions: {len(bad)}.")
    print(f"Wrote {out / 'results_long.csv'} and {out / 'summary.md'}")


if __name__ == "__main__":
    main()
