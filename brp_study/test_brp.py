"""Unit tests for the BRP study. Run with:  python -m unittest brp_study.test_brp -v  (from the project root)
or:  python -m unittest discover -s brp_study -v
"""

import unittest
from pathlib import Path

from brp import (Instance, load_instances, verify, solve_minmax, solve_astar,
                 solve_glah, solve_bfs, condense, badly_placed)

DATA = Path(__file__).resolve().parent.parent / "data" / "instances"


def make_instance(stacks, H, file="inline"):
    N = sum(len(s) for s in stacks)
    return Instance(file, 0, len(stacks), H, N, tuple(tuple(s) for s in stacks))


# The example used in data/instances/LEIAME.md: target 1 sits at the bottom of stack 3.
README_EXAMPLE = make_instance([[8, 7, 6], [2], [1, 3, 4, 5]], H=4)


class VerifyTests(unittest.TestCase):
    def test_no_moves_needed_when_targets_are_on_top(self):
        inst = make_instance([[1], [2]], H=3)  # 1 and 2 are on top, retrieved for free
        ok, _ = verify(inst, [])
        self.assertTrue(ok)

    def test_move_from_non_target_stack_is_rejected(self):
        inst = make_instance([[1, 3], [2]], H=3)
        # the target 1 is under 3 in stack 1, so moving from stack 2 is illegal
        ok, msg = verify(inst, [(2, 1)])
        self.assertFalse(ok)
        self.assertIn("target", msg)

    def test_full_destination_is_rejected(self):
        inst = make_instance([[1, 3], [2, 4]], H=2)
        ok, msg = verify(inst, [(1, 2)])
        self.assertFalse(ok)
        self.assertIn("full", msg)

    def test_incomplete_sequence_is_rejected(self):
        ok, msg = verify(README_EXAMPLE, [])
        self.assertFalse(ok)
        self.assertIn("not empty", msg)


class MinMaxTests(unittest.TestCase):
    def test_readme_example_is_feasible(self):
        res = solve_minmax(README_EXAMPLE)
        self.assertTrue(verify(README_EXAMPLE, res.moves)[0])

    def test_minmax_rule_prefers_supporting_stack(self):
        # blocker 9 on top of target stack; stack 2 has min 10 > 9 -> must go there
        inst = make_instance([[1, 9], [10, 11]], H=3)
        res = solve_minmax(inst)
        self.assertEqual(res.moves[0], (1, 2))
        self.assertTrue(verify(inst, res.moves)[0])


class AStarTests(unittest.TestCase):
    def test_astar_matches_bfs_on_small_instances(self):
        small = load_instances(DATA / "brp_W3_H4_N8.json")[:4]
        for inst in small:
            res = solve_astar(inst, time_limit=30)
            self.assertEqual(res.status, "optimal")
            self.assertEqual(res.reshuffles, solve_bfs(inst), msg=f"id={inst.inst_id}")
            self.assertTrue(verify(inst, res.moves)[0])

    def test_astar_matches_bfs_on_readme_example(self):
        res = solve_astar(README_EXAMPLE, time_limit=30)
        self.assertEqual(res.reshuffles, solve_bfs(README_EXAMPLE))
        self.assertTrue(verify(README_EXAMPLE, res.moves)[0])

    def test_optimum_never_above_heuristics(self):
        inst = load_instances(DATA / "brp_W4_H4_N10.json")[0]
        opt = solve_astar(inst, time_limit=30).reshuffles
        self.assertLessEqual(opt, solve_minmax(inst).reshuffles)
        self.assertLessEqual(opt, solve_glah(inst, depth=3).reshuffles)


class GLAHTests(unittest.TestCase):
    def test_glah_solutions_verify_and_are_not_worse_than_its_start(self):
        for name in ["brp_W3_H4_N8.json", "brp_W4_H4_N10.json"]:
            for inst in load_instances(DATA / name)[:3]:
                res = solve_glah(inst, depth=3, time_limit=30)
                self.assertTrue(verify(inst, res.moves)[0], msg=f"{name} id={inst.inst_id}")
                self.assertGreaterEqual(res.reshuffles, solve_astar(inst, 30).reshuffles)

    def test_condense_keeps_solution_valid(self):
        for inst in load_instances(DATA / "brp_W3_H4_N8.json")[:3]:
            moves = solve_minmax(inst).moves
            condensed = condense(inst, moves)
            self.assertLessEqual(len(condensed), len(moves))
            self.assertTrue(verify(inst, condensed)[0])

    def test_badly_placed_counts_containers_above_smaller_labels(self):
        # bottom -> top. A container is badly placed if a smaller label lies below it.
        self.assertEqual(badly_placed([(1, 3, 2)]), 2)   # 3 and 2 both sit above 1
        self.assertEqual(badly_placed([(3, 2, 1)]), 0)   # every container is above only larger labels
        self.assertEqual(badly_placed([(1, 2, 3)]), 2)


class DataTests(unittest.TestCase):
    def test_all_data_files_load_and_are_consistent(self):
        files = sorted(DATA.glob("brp_*.json"))
        self.assertEqual(len(files), 17)  # 5 files in set A + 12 files in set B (data/instances/LEIAME.md)
        total = 0
        for f in files:
            insts = load_instances(f)
            self.assertEqual(len(insts), 10, msg=f.name)
            total += len(insts)
        self.assertEqual(total, 170)


if __name__ == "__main__":
    unittest.main()
