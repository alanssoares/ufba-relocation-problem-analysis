"""Run the common comparison protocol on the instance pack in data/instances.

Methods: Min-Max (Caserta et al., 2012), A* (exact), GLAH-R with depth D=3 and D=4
(Jin, Zhu & Lim, 2015, restricted adaptation). Every solution is re-verified with
an independent simulator before it enters the tables.

Usage (from the project root):
    python brp_study/run_experiments.py
    python brp_study/run_experiments.py --time-limit 30 --only W3_H4
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

FIELDS = ["file", "W", "H", "N", "id", "method", "status", "reshuffles", "verified",
          "z_star", "z_star_source", "gap_pct", "time_s", "lower_bound", "nodes", "moves"]


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


def summarize(rows: list[dict]) -> str:
    methods = []
    for r in rows:
        if r["method"] not in methods:
            methods.append(r["method"])

    def group(filter_fn):
        return [r for r in rows if filter_fn(r)]

    lines = ["# BRP comparison summary", ""]
    lines.append("## Overall (all instances)")
    lines.append("")
    lines.append("| Method | Instances | Verified | Mean reshuffles | Mean gap (%) | Max gap (%) | Matches Z* (gap 0) | Better than Min-Max | Worse than Min-Max | Mean time (s) | Max time (s) | Timeouts |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
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
    lines.append("| File | W | H | N | Method | Mean reshuffles | Mean gap (%) | Mean time (s) | A* proved optimal | Timeouts |")
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
            proved = sum(1 for r in rs if r["method"] == "A*" and r["status"] == "optimal")
            timeouts = sum(1 for r in rs if r["status"] == "timeout")
            first = rs[0]
            mean_rs = f"{statistics.fmean(recs):.2f}" if recs else "-"
            mean_gap = f"{statistics.fmean(gaps):.2f}" if gaps else "-"
            lines.append(
                f"| {f} | {first['W']} | {first['H']} | {first['N']} | {m} | {mean_rs} | {mean_gap} | "
                f"{statistics.fmean(times):.3f} | {proved if m == 'A*' else '-'} | {timeouts} |"
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
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in Path(args.data_dir).glob("brp_*.json") if args.only in p.name)
    if not files:
        sys.exit("no instance files matched")

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
