"""Unit tests for the unrestricted BRP (brp_unrestricted.py). Run from the project root with:
    python -m unittest discover -s brp_study -v
"""

import unittest
from pathlib import Path

from brp import Instance, load_instances, verify, solve_astar
from brp_unrestricted import (lower_bound_u, solve_bfs_u, solve_astar_u, solve_glah_u,
                              evaluate_u, classify_relocations, candidate_relocations,
                              condense_u, PAPER_LIMITS, _start_state)

DATA = Path(__file__).resolve().parent.parent / "data" / "instances"


def make_instance(stacks, H):
    N = sum(len(s) for s in stacks)
    return Instance("inline", 0, len(stacks), H, N, tuple(tuple(s) for s in stacks))


README_EXAMPLE = make_instance([[8, 7, 6], [2], [1, 3, 4, 5]], H=4)

# Case 2 of the evaluation heuristic: blocker 5 has no supporting stack, but the
# well placed top 3 of stack 2 can go onto stack 3 (gmin 4 > 3), after which
# stack 2 (only 6 left) supports 5. Expected: <3: 2->3>, <5: 1->2>, then all
# containers are retrieved without further relocations.
CASE2 = make_instance([[1, 5], [6, 3], [4], [2]], H=3)

# Case 1 with gap utilisation: blocker 3 goes to stack 2 (gmin 5). Before that,
# the badly placed top 4 of stack 3 (3 < 4 < 5) fills the gap in stack 2.
CASE1_GAP = make_instance([[1, 3], [5], [2, 4]], H=4)


def small_instances():
    return (load_instances(DATA / "brp_W3_H4_N8.json")
            + load_instances(DATA / "brp_W4_H4_N10.json")[:5]
            + [README_EXAMPLE, CASE2, CASE1_GAP])


class VerifyUnrestrictedTests(unittest.TestCase):
    def test_move_from_non_target_stack_is_accepted_only_when_unrestricted(self):
        inst = make_instance([[1, 3], [2]], H=3)
        # 2 -> stack 1 is not allowed in the restricted variant (target 1 is in stack 1)
        moves = [(2, 1), (1, 2), (1, 2)]  # 2 onto 3, then 2 and 3 to stack 2... check below
        self.assertFalse(verify(inst, moves, restricted=True)[0])
        ok, msg = verify(inst, [(1, 2)], restricted=False)  # 3 onto 2, 1 leaves, then 3 blocks 2
        self.assertFalse(ok)
        self.assertIn("not empty", msg)
        self.assertTrue(verify(inst, [(1, 2), (2, 1)], restricted=False)[0])

    def test_unrestricted_still_checks_height_and_empty_source(self):
        inst = make_instance([[1, 3], [2, 4]], H=2)
        self.assertIn("full", verify(inst, [(1, 2)], restricted=False)[1])
        inst = make_instance([[2, 1], []], H=2)  # everything leaves at once
        self.assertIn("empty", verify(inst, [(2, 1)], restricted=False)[1])

    def test_default_is_still_restricted(self):
        inst = make_instance([[1, 3], [2]], H=3)
        self.assertFalse(verify(inst, [(2, 1)])[0])


class LowerBoundTests(unittest.TestCase):
    def test_binary_term_applies_when_no_stack_can_take_a_top(self):
        # tops 3 and 4 are both larger than every stack minimum (1, 2), no empty stack
        inst = make_instance([[1, 3], [2, 4]], H=3)
        self.assertEqual(lower_bound_u(_start_state(inst)), 3)  # 2 badly placed + 1
        self.assertLessEqual(3, solve_bfs_u(inst))  # optimum is 4: the bound is valid, not tight

    def test_binary_term_off_with_an_empty_stack(self):
        self.assertEqual(lower_bound_u(((1, 3), (2, 4), ())), 2)

    def test_lower_bound_never_exceeds_optimum(self):
        for inst in small_instances():
            self.assertLessEqual(lower_bound_u(_start_state(inst)), solve_bfs_u(inst))


class AStarUnrestrictedTests(unittest.TestCase):
    def test_astar_matches_bfs(self):
        for inst in small_instances():
            opt = solve_bfs_u(inst)
            res = solve_astar_u(inst, time_limit=30)
            self.assertEqual(res.status, "optimal")
            self.assertEqual(res.reshuffles, opt, msg=f"{inst.file} id={inst.inst_id}")
            self.assertTrue(verify(inst, res.moves, restricted=False)[0])

    def test_astar_with_incumbent_stays_optimal(self):
        for inst in small_instances():
            inc = solve_glah_u(inst, depth=3).moves
            res = solve_astar_u(inst, time_limit=30, incumbent=inc)
            self.assertEqual(res.status, "optimal")
            self.assertEqual(res.reshuffles, solve_bfs_u(inst))
            self.assertTrue(verify(inst, res.moves, restricted=False)[0])

    def test_unrestricted_optimum_never_above_restricted(self):
        strictly_better = 0
        for inst in load_instances(DATA / "brp_W3_H4_N8.json") + load_instances(DATA / "brp_W4_H4_N10.json"):
            u = solve_astar_u(inst, time_limit=30).reshuffles
            r = solve_astar(inst, time_limit=30).reshuffles
            self.assertLessEqual(u, r)
            strictly_better += u < r
        self.assertGreater(strictly_better, 0)


class EvaluationHeuristicTests(unittest.TestCase):
    def test_case2_moves_a_well_placed_top_to_an_assistant_stack(self):
        moves = evaluate_u(CASE2.stacks, CASE2.N, CASE2.H)
        self.assertEqual(moves, [(2, 3), (1, 2)])
        self.assertTrue(verify(CASE2, moves, restricted=False)[0])
        self.assertFalse(verify(CASE2, moves, restricted=True)[0])  # 3 is not above the target

    def test_case1_with_gap_utilisation(self):
        moves = evaluate_u(CASE1_GAP.stacks, CASE1_GAP.N, CASE1_GAP.H)
        self.assertEqual(moves, [(3, 2), (1, 2)])
        self.assertTrue(verify(CASE1_GAP, moves, restricted=False)[0])

    def test_evaluation_solutions_verify_on_all_files_sample(self):
        for f in sorted(DATA.glob("brp_*.json")):
            for inst in load_instances(f)[:2]:
                moves = evaluate_u(inst.stacks, inst.N, inst.H)
                self.assertTrue(verify(inst, moves, restricted=False)[0], msg=f"{f.name} id={inst.inst_id}")


class LookAheadTests(unittest.TestCase):
    def test_relocation_categories(self):
        # stack 1: target 1 under 3 | stack 2: 2 under 4 | stack 3: 5 alone
        cats = classify_relocations([[1, 3], [2, 4], [5]], N=5, H=3)
        self.assertEqual(cats["FT-BG"], [(0, 2)])   # 3 onto 5
        self.assertEqual(cats["FT-BB"], [(0, 1)])   # 3 onto 2..4
        self.assertEqual(cats["NF-BG"], [(1, 2)])   # 4 onto 5
        self.assertEqual(cats["NF-BB"], [(1, 0)])   # 4 onto 1..3
        self.assertEqual(sorted(cats["GB"]), [(2, 0), (2, 1)])  # 5 leaves its own stack, lands badly
        self.assertEqual(cats["GG"], [])

    def test_good_good_relocation_is_detected(self):
        cats = classify_relocations(CASE2.stacks, CASE2.N, CASE2.H)
        self.assertIn((1, 2), cats["GG"])  # 3: stack 2 -> stack 3 (onto 4)

    def test_candidate_list_respects_limits_and_adds_advice(self):
        stacks = [list(s) for s in CASE2.stacks]
        cand = candidate_relocations(stacks, CASE2.N, CASE2.H, {k: 0 for k in PAPER_LIMITS}, (1, 2))
        self.assertEqual(cand, [(1, 2)])
        cand = candidate_relocations(stacks, CASE2.N, CASE2.H, PAPER_LIMITS, (1, 2))
        self.assertEqual(len(cand), len(set(cand)))


class GLAHUnrestrictedTests(unittest.TestCase):
    def test_glah_u_verifies_and_is_between_optimum_and_evaluation(self):
        for inst in small_instances():
            for depth in (3, 4):
                res = solve_glah_u(inst, depth=depth, time_limit=30)
                self.assertTrue(verify(inst, res.moves, restricted=False)[0])
                self.assertGreaterEqual(res.reshuffles, solve_bfs_u(inst))
                self.assertLessEqual(res.reshuffles, len(evaluate_u(inst.stacks, inst.N, inst.H)))

    def test_seed_never_makes_it_worse(self):
        inst = load_instances(DATA / "brp_W5_H5_N18.json")[0]
        seed = solve_astar(inst, time_limit=30).moves  # restricted optimum, also U-feasible
        res = solve_glah_u(inst, depth=3, seed=seed)
        self.assertLessEqual(res.reshuffles, len(seed))
        self.assertTrue(verify(inst, res.moves, restricted=False)[0])

    def test_condensation_merges_consecutive_moves(self):
        # 3 goes onto 2 (1 leaves), then onto 4 (2, 3 and 4 leave): the pair merges into 3: 1->3
        inst = make_instance([[1, 3], [2], [4]], H=3)
        self.assertEqual(condense_u(inst.stacks, [(1, 2), (2, 1)], inst.H), [(1, 2), (2, 1)])  # s3 == s1
        self.assertEqual(condense_u(inst.stacks, [(1, 2), (2, 3)], inst.H), [(1, 3)])


if __name__ == "__main__":
    unittest.main()
