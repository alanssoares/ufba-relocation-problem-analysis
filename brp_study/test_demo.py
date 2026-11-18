"""Tests for the demo helpers used by notebooks/brp_demo.ipynb."""

import unittest

from demo import (list_files, get_instance, instance_from_stacks, render, replay, solve_all,
                  table_md, find)


class DemoTests(unittest.TestCase):
    def test_files_and_instances_load(self):
        self.assertEqual(len(list_files()), 17)
        inst = get_instance("brp_W3_H4_N8.json", 8)
        self.assertEqual((inst.W, inst.H, inst.N), (3, 4, 8))
        with self.assertRaises(KeyError):
            get_instance("brp_W3_H4_N8.json", 11)

    def test_instance_from_stacks_validates_labels_and_height(self):
        inst = instance_from_stacks([[8, 7, 6], [2], [1, 3, 4, 5]], H=4)
        self.assertEqual(inst.N, 8)
        with self.assertRaises(ValueError):
            instance_from_stacks([[1, 3]], H=4)       # label 2 missing
        with self.assertRaises(ValueError):
            instance_from_stacks([[1, 2, 3]], H=2)    # stack taller than H

    def test_render_draws_bottom_at_the_bottom(self):
        lines = render([[1, 2], [3]], H=3).splitlines()
        self.assertEqual(lines[0].split(), ["2"])
        self.assertEqual(lines[1].split(), ["1", "3"])
        self.assertIn("P1", lines[-1])

    def test_solve_all_and_replay_on_the_findings_example(self):
        inst = get_instance("brp_W3_H4_N8.json", 8)
        rows = solve_all(inst, time_limit=10)
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(r["verified"] for r in rows))
        self.assertEqual(find(rows, "A*")["reshuffles"], 5)
        self.assertEqual(find(rows, "A*-U")["reshuffles"], 4)
        self.assertIn("| A*-U | 4 |", table_md(rows))
        text = replay(inst, find(rows, "A*-U")["moves"], restricted=False)
        self.assertIn("verificação: OK", text)
        self.assertIn("antecipada", text)
        self.assertIn("Pátio vazio.", text)


class VisualPageTests(unittest.TestCase):
    def test_page_data_is_complete_and_verified(self):
        from pathlib import Path
        from make_visual import build, HIGHLIGHTS
        here = Path(__file__).resolve().parent
        data = build(here.parent / "data" / "instances", here / "results", [], time_limit=10)
        self.assertEqual(len(data["instances"]), 171)  # 170 data instances + the LEIAME example
        self.assertEqual(len(data["highlights"]), len(HIGHLIGHTS))
        for x in data["instances"]:
            self.assertEqual(len(x["methods"]), 7, msg=x["key"])
            for m in x["methods"]:
                if m["moves"] is not None:
                    self.assertTrue(m["verified"], msg=f"{x['key']} {m['name']}")


if __name__ == "__main__":
    unittest.main()
