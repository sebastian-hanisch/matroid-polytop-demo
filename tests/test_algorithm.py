"""Kern: Ecken, Greedy, Dual, Facetten, Kanten, Trennung, Spannbaum-LP; jeweils an Handbeispielen (conftest.py)."""

import numpy as np
import pytest

import mpo_algorithm as A


def test_u23_hat_sieben_ecken_und_sieben_facetten(u23):
    n, ok, r = u23
    verts = A.vertices([ok], n)
    assert verts == A.indep_indicators(ok, n) and len(verts) == 7
    f = A.facets(ok, r, n)
    assert sorted(f["nn"]) == [0, 1, 2] and sorted(f["rank"]) == [1, 2, 4, 7] and f["dim"] == 3 and f["total"] == 3 + 7
    assert len(f["nn"]) + len(f["rank"]) == 7                        # x_e ≥ 0, x_e ≤ 1 (die drei Einzelelemente) und x(E) ≤ 2


def test_u23_greedy_und_dual_bei_den_gewichten_5_3_1(u23):
    n, ok, r = u23
    mask, value, order = A.greedy(ok, n, [5, 3, 1])
    assert (mask, value, order) == (0b011, 8, [0, 1, 2])
    dual = A.greedy_dual(r, n, [5, 3, 1])
    assert dual == [(0b001, 2), (0b111, 3)]                          # y auf {a} = 5 − 3, auf E = 3 − 1 + 1 (Hülle von {a, b} ist E)
    chk = A.dual_check(r, n, [5, 3, 1], dual)
    assert chk == {"feasible": True, "value": 8, "integral": True}
    assert A.lp_max(r, n, [5, 3, 1])[0] == pytest.approx(8)


def test_u23_gleiche_gewichte_und_negative_gewichte(u23):
    n, ok, r = u23
    assert A.greedy(ok, n, [4, 4, 4])[:2] == (0b011, 8)                # Gleichstand: kleinere Nummer zuerst
    assert A.greedy(ok, n, [4, 0, -3])[:2] == (0b001, 4)                # nur positive Gewichte
    assert A.greedy(ok, n, [4, 0, -3], base=True)[:2] == (0b011, 4)     # Basis: auch Gewicht 0 (a, dann b; c passt nicht mehr, Rang 2)
    assert A.lp_max(r, n, [4, 4, 4])[0] == pytest.approx(8)


def test_oktaeder_u24_hat_6_ecken_und_12_kanten_gleich_basenaustausch():
    mat = A.named_matroid("u24")
    n, ok = mat["n"], mat["ok"]
    r = A.rank_table(ok, n)
    verts = A.polytope_vertices(ok, r, n, True)
    edges = A.polytope_edges(ok, r, n, True)
    assert len(verts) == 6 and len(edges) == 12
    assert set(edges) == set(A.exchange_pairs(ok, r, n))
    assert A.facets(ok, r, n, True)["dim"] == 3


def test_tetraeder_und_pyramide():
    for key, verts, edges in (("u14", 4, 6), ("u24p", 5, 8)):
        mat = A.named_matroid(key)
        r = A.rank_table(mat["ok"], mat["n"])
        assert len(A.polytope_vertices(mat["ok"], r, mat["n"], True)) == verts and len(A.polytope_edges(mat["ok"], r, mat["n"], True)) == edges, key


def test_zusammenhaengende_flats_von_u23(u23):
    n, ok, r = u23
    flats, conn = A.flats_of(ok, r, n)
    assert sorted(flats) == [1, 2, 4, 7] and sorted(conn) == [1, 2, 4, 7]     # Einzelelemente und E; Paare sind keine Flats (ihre Hülle ist E)


def test_matroid_mit_koloop_hat_nicht_zusammenhaengendes_gesamt_flat():
    ok = A.partition_table(2, [0, 1], {0: 1, 1: 1})                 # zwei Koloops: der Würfel [0,1]^2
    r = A.rank_table(ok, 2)
    flats, conn = A.flats_of(ok, r, 2)
    assert sorted(flats) == [1, 2, 3] and sorted(conn) == [1, 2]       # E = {a, b} zerfällt in zwei Teile mit r(A) + r(B) = r(E)
    f = A.facets(ok, r, 2)
    assert sorted(f["rank"]) == [1, 2] and sorted(f["nn"]) == [0, 1]


def test_trennung_dreieck(dreieck):
    n, edges, ok, r = dreieck
    val, mask = A.separate(r, 3, [1.0, 1.0, 1.0])
    assert val == pytest.approx(-1.0) and mask == 0b111               # r(E) = 2 < x(E) = 3
    assert A.separate(r, 3, [0.5, 0.5, 0.5])[0] == pytest.approx(0.5)   # r(E) − x(E) = 2 − 1,5; Einzelelemente 1 − 0,5
    assert A.in_hull(ok, 3, [2 / 3, 2 / 3, 2 / 3]) and not A.in_hull(ok, 3, [1, 1, 1])


def test_spannbaum_lp_k5_handbeispiel(k5):
    n, edges, cost = k5
    opt, tree = A.kruskal(n, edges, cost)
    assert opt == 5 and A.elements(tree, 10) == [0, 1, 2, 9]            # 03 und 34 (Kosten 0), 01 (2), 02 (3); 04, 13, 14 würden Kreise schließen
    cut, x = A.tree_lp(n, edges, cost, "cut")
    assert cut == pytest.approx(4.5) and A.is_fractional(x)
    assert A.tree_lp(n, edges, cost, "partition")[0] == pytest.approx(5.0)
    assert A.tree_lp(n, edges, cost, "rank")[0] == pytest.approx(5.0)


def test_schnittebenenlauf_k5_endet_beim_optimum(k5):
    n, edges, cost = k5
    rounds = A.cutting_plane(n, edges, cost)
    assert rounds[0]["value"] == pytest.approx(4.5) and rounds[0]["violation"] is not None and rounds[0]["violation"][0] > 0
    assert rounds[-1]["violation"] is None and rounds[-1]["value"] == pytest.approx(5.0)
    assert [r["value"] for r in rounds] == sorted(r["value"] for r in rounds)      # der Wert wächst mit jeder Ebene
    assert len(rounds) <= 6


def test_verletzte_knotenmenge_beim_halben_dreieck():
    edges = [(0, 1), (1, 2), (0, 2)]
    assert A.violated_set(3, edges, np.array([1.0, 1.0, 1.0])) == (pytest.approx(1.0), 0b111)
    assert A.violated_set(3, edges, np.array([0.5, 0.5, 0.5])) is None
    assert A.violated_set(3, edges, np.array([1.0, 1.0, 0.0])) is None


def test_ein_element_matroid_und_schlinge():
    ok = np.array([True, True])                                      # ein freies Element
    r = A.rank_table(ok, 1)
    assert A.vertices([ok], 1) == {(0.0,), (1.0,)}
    loop = np.array([True, False])
    assert A.vertices([loop], 1) == {(0.0,)}
    assert A.facets(loop, A.rank_table(loop, 1), 1)["total"] == 0
    assert A.greedy_dual(r, 1, [3]) == [(1, 3)]


def test_dreieck_von_drei_partitionsmatroiden_hat_gebrochene_ecke():
    t = A.triangle_example()
    assert t["fractional"] == [(0.5, 0.5, 0.5)] and len(t["common"]) == 4 and len(t["vertices"]) == 5


def test_unbekannte_formulierung_und_matroid():
    with pytest.raises(ValueError):
        A.tree_rows(4, [(0, 1)], "xyz")
    with pytest.raises(ValueError):
        A.named_matroid("xyz")
