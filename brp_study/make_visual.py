"""Build a self-contained HTML page that animates the solution of every method.

The page (default: visual/brp_visual.html) needs no server, no framework and no
internet connection: open it in a browser. It shows one panel per method
(restricted: Min-Max, A*, GLAH-R D=3/D=4; unrestricted: GLAH-U D=3/D=4, A*-U),
all advancing together one relocation at a time.

Solutions come from the saved experiment results (results/results_long.csv and
results/unrestricted_long.csv, 30 s budget per method), so the page shows exactly
the runs reported in the README. Every solution is verified again here before
it is embedded. Extra instances typed with --custom are solved on the spot.

Usage (from the project root):
    python brp_study/make_visual.py
    python brp_study/make_visual.py --custom "[[8,7,6],[2],[1,3,4,5]]:4" --time-limit 10
    python brp_study/make_visual.py --out visual/brp_visual.html
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from brp import load_instances, verify  # noqa: E402
from demo import instance_from_stacks, solve_all  # noqa: E402

RESTRICTED = ["Min-Max", "A*", "GLAH-R (D=3)", "GLAH-R (D=4)"]
UNRESTRICTED = ["GLAH-U (D=3)", "GLAH-U (D=4)", "A*-U"]

# Instances worth showing first in class: (file, id, short description)
HIGHLIGHTS = [
    ("brp_W3_H4_N8.json", 8, "Exemplo do ACHADOS: antecipar economiza 1 movimento"),
    ("exemplo_LEIAME", 1, "Exemplo do LEIAME.md (exercício de aula)"),
    ("brp_W5_H5_N18.json", 1, "Conjunto A, maior arquivo"),
    ("brp_W7_H5_N31.json", 10, "Maior ganho provado do irrestrito"),
    ("brp_W7_H7_N32.json", 6, "Pior caso do GLAH-U frente ao ótimo"),
    ("brp_W7_H8_N49.json", 1, "Maior instância: os exatos esgotam o tempo"),
]

LEIAME_EXAMPLE = ([[8, 7, 6], [2], [1, 3, 4, 5]], 4)


def _load_results(path: Path) -> dict:
    out: dict = {}
    if not path.exists():
        return out
    with path.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["file"], int(r["id"]), r["method"])] = r
    return out


def _method_entry(inst, name: str, variant: str, moves, status: str, time_s, lb) -> dict:
    ok = moves is not None and verify(inst, moves, restricted=(variant == "R"))[0]
    return {"name": name, "variant": variant, "moves": moves, "status": status,
            "verified": ok, "time": time_s, "lb": lb}


def from_results(inst, res_r: dict, res_u: dict) -> dict | None:
    """Panel data of one data-file instance, read from the saved results."""
    methods = []
    z = {}
    for names, variant, res in ((RESTRICTED, "R", res_r), (UNRESTRICTED, "U", res_u)):
        for name in names:
            r = res.get((inst.file, inst.inst_id, name))
            if r is None:
                continue
            moves = [tuple(m) for m in json.loads(r["moves"])] if r["moves"] else None
            lb = int(r["lower_bound"]) if r["lower_bound"] else None
            methods.append(_method_entry(inst, name, variant, moves, r["status"], float(r["time_s"]), lb))
            z[variant] = (int(r["z_star"]), r["z_star_source"])
    if not methods:
        return None
    return {"key": f"{inst.file}#{inst.inst_id}", "file": inst.file, "id": inst.inst_id,
            "label": f"{inst.file.replace('.json', '')} · id {inst.inst_id}",
            "W": inst.W, "H": inst.H, "N": inst.N, "stacks": [list(s) for s in inst.stacks],
            "zr": z.get("R", (None, None))[0], "zr_src": z.get("R", (None, None))[1],
            "zu": z.get("U", (None, None))[0], "zu_src": z.get("U", (None, None))[1],
            "methods": methods}


def solve_live(inst, name: str, inst_id: int, label: str, time_limit: float) -> dict:
    """Panel data of a typed-in instance, solved now with every method."""
    rows = solve_all(inst, time_limit=time_limit)
    methods, z = [], {}
    for r in rows:
        variant = "R" if r["variant"] == "restrita" else "U"
        methods.append(_method_entry(inst, r["method"], variant, r["moves"], r["status"], r["time_s"],
                                     r["lower_bound"]))
    for variant, exact in (("R", "A*"), ("U", "A*-U")):
        ex = next(m for m in methods if m["name"] == exact)
        best = min(len(m["moves"]) for m in methods if m["variant"] == variant and m["moves"] is not None)
        z[variant] = (len(ex["moves"]), "A* optimum") if ex["status"] == "optimal" else (best, "best known")
    return {"key": f"{name}#{inst_id}", "file": name, "id": inst_id, "label": label,
            "W": inst.W, "H": inst.H, "N": inst.N, "stacks": [list(s) for s in inst.stacks],
            "zr": z["R"][0], "zr_src": z["R"][1], "zu": z["U"][0], "zu_src": z["U"][1],
            "methods": methods}


def build(data_dir: Path, results_dir: Path, customs: list[tuple[list, int]], time_limit: float) -> dict:
    res_r = _load_results(results_dir / "results_long.csv")
    res_u = _load_results(results_dir / "unrestricted_long.csv")
    instances = []
    for i, (stacks, H) in enumerate([LEIAME_EXAMPLE] + customs, start=1):
        inst = instance_from_stacks(stacks, H)
        name = "exemplo_LEIAME" if i == 1 else "personalizada"
        inst_id = 1 if i == 1 else i - 1
        label = "Exemplo do LEIAME.md" if i == 1 else f"Instância personalizada {inst_id}"
        instances.append(solve_live(inst, name, inst_id, label, time_limit))
    for path in sorted(data_dir.glob("brp_*.json")):
        for inst in load_instances(path):
            entry = from_results(inst, res_r, res_u)
            if entry is not None:
                instances.append(entry)

    by_key = {x["key"]: x for x in instances}
    highlights = []
    for file, inst_id, desc in HIGHLIGHTS:
        x = by_key.get(f"{file}#{inst_id}")
        if x is None:
            continue
        x["note"] = f"{desc}. Referência: {x['zr']} movimentos no restrito, {x['zu']} no irrestrito."
        highlights.append({"key": x["key"], "label": f"{desc} ({x['label']})"})
    return {"instances": instances, "highlights": highlights}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", default=str(HERE.parent / "data" / "instances"))
    ap.add_argument("--results-dir", default=str(HERE / "results"))
    ap.add_argument("--out", default=str(HERE.parent / "visual" / "brp_visual.html"))
    ap.add_argument("--custom", action="append", default=[],
                    help='extra instance "STACKS:H", stacks bottom -> top, e.g. "[[2,1],[3]]:3" (repeatable)')
    ap.add_argument("--time-limit", type=float, default=10.0, help="seconds per method for --custom instances")
    args = ap.parse_args()

    customs = []
    for spec in args.custom:
        stacks, H = spec.rsplit(":", 1)
        customs.append((ast.literal_eval(stacks), int(H)))

    data = build(Path(args.data_dir), Path(args.results_dir), customs, args.time_limit)
    bad = [(x["key"], m["name"]) for x in data["instances"] for m in x["methods"]
           if m["moves"] is not None and not m["verified"]]
    if bad:
        sys.exit(f"unverified solutions, page not written: {bad}")

    template = (HERE / "visual_template.html").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("__DATA__", payload)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    n_sol = sum(1 for x in data["instances"] for m in x["methods"] if m["moves"] is not None)
    print(f"Wrote {out} ({out.stat().st_size / 1024:.0f} KB): {len(data['instances'])} instances, "
          f"{n_sol} verified solutions, {len(data['highlights'])} highlights.")


if __name__ == "__main__":
    main()
