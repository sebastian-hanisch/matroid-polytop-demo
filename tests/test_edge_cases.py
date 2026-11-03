"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): kleinste Fälle, Schlingen und Koloops, Gleichstände, Reglergrenzen, Spielwiese."""

import numpy as np
import pytest

import mpo_algorithm as A
import mpo_constants as C
import mpo_evaluation as ev
from mpo_systems import get_net


def test_two_elements_free_and_parallel():
    free = np.ones(4, dtype=bool)
    assert A.vertices([free], 2) == {(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)}
    par = np.array([True, True, True, False])                             # a ∥ b: höchstens eins
    r = A.rank_table(par, 2)
    assert A.vertices([par], 2) == {(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)}
    assert A.polytope_edges(par, r, 2, True) == [(1, 2)] and A.exchange_pairs(par, r, 2) == [(1, 2)]
    assert A.facets(par, r, 2)["nn"] == [0, 1] and A.facets(par, r, 2)["rank"] == [3]       # x_a, x_b ≥ 0 und x_a + x_b ≤ 1 (x_e ≤ 1 ist überflüssig)


def test_loops_are_excluded_from_the_dimension_and_the_facets():
    ok = np.array([m & 1 == 0 and bin(m).count("1") <= 1 for m in range(8)])         # a ist eine Schlinge, b und c parallel
    r = A.rank_table(ok, 3)
    f = A.facets(ok, r, 3)
    assert f["dim"] == 2 and sorted(f["nn"]) == [1, 2] and f["rank"] == [6]
    assert A.vertices([ok], 3) == {(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)}


def test_the_zero_matroid_has_one_vertex_and_no_facets():
    zero = np.array([True] + [False] * 3)
    r = A.rank_table(zero, 2)
    assert A.vertices([zero], 2) == {(0.0, 0.0)} and A.facets(zero, r, 2)["total"] == 0 and A.greedy(zero, 2, [3, 4])[:2] == (0, 0)
    dual = A.greedy_dual(r, 2, [3, 4])
    assert dual == [(0b11, 4)] and A.dual_check(r, 2, [3, 4], dual) == {"feasible": True, "value": 0, "integral": True}       # alles ist Hülle der leeren Menge


def test_greedy_tie_breaks_by_index_and_zero_weights_are_skipped_in_the_independence_polytope():
    ok = A.uniform_table(4, 2)
    assert A.greedy(ok, 4, [3, 3, 3, 3])[0] == 0b0011
    assert A.greedy(ok, 4, [0, 0, 5, 0])[0] == 0b0100
    assert A.greedy_dual(A.rank_table(ok, 4), 4, [0, 0, 0, 0]) == []


def test_spanning_tree_lp_on_a_tree_and_a_triangle():
    assert A.tree_lp(3, [(0, 1), (1, 2)], [4, 5], "cut")[0] == pytest.approx(9) and A.kruskal(3, [(0, 1), (1, 2)], [4, 5]) == (9, 0b11)
    tri = [(0, 1), (1, 2), (0, 2)]
    for kind in ("cut", "partition", "rank"):
        assert A.tree_lp(3, tri, [1, 2, 3], kind)[0] == pytest.approx(3), kind          # zwei billigste Kanten


def test_plan_sizes_and_fixed_k5():
    assert [get_net("plan", n, 8).m for n in range(C.N_MIN, C.N_MAX + 1)] == [10, 12, 14]
    assert get_net("k5", 6, 1).edges == get_net("k5", 8, 99).edges and get_net("k5", 6, 1).m == 10
    with pytest.raises(ValueError):
        get_net("kreis", 7, 8)


def test_every_regler_corner_gives_consistent_numbers():
    for n in (C.N_MIN, C.N_MAX):
        for form in C.FORMS:
            for seed in (0, C.SEED_MAX):
                s = ev.Settings(n, seed, "plan", form)
                v = ev.lp_view(s)
                assert v["value"] <= v["opt"] + 1e-6, (n, form, seed)
                assert ev.verdict_lp(s, v)[0] != "error"
                rounds = ev.rounds_view(s)
                assert rounds[-1]["violation"] is None and abs(rounds[-1]["value"] - v["opt"]) < 1e-6


def test_play_view_without_and_with_overlap_and_a_full_tree():
    s = ev.Settings(**C.PRESETS["Handbeispiel K5"])
    assert ev.play_view(s, (), ())["sum"] == 0 and ev.play_view(s, (), ())["node"] is None
    v = ev.play_view(s, (0, 1, 2, 9), ())
    assert v["node"] is None and v["sum"] == 4
    both = ev.play_view(s, (0,), (0, 1))
    assert both["x"][0] == 1.0 and both["x"][1] == 0.5 and both["sum"] == 1.5
    assert ev.play_view(s, (2, 3, 9), ())["node"][1] == 0b11001


def test_the_two_polytope_helpers_on_the_smallest_cases():
    assert A.pair_row(1, 1) == {"n": 1, "pairs": 4, "integral": 4, "common": 4}
    assert A.triple_row(2) == {"n": 2, "triples": 125, "fractional": 0}


def test_dual_check_catches_an_infeasible_dual():
    ok = A.uniform_table(3, 2)
    r = A.rank_table(ok, 3)
    assert A.dual_check(r, 3, [5, 3, 1], [(0b001, 2)])["feasible"] is False
    assert A.dual_check(r, 3, [5, 3, 1], [(0b001, 2.5), (0b111, 3)])["integral"] is False
