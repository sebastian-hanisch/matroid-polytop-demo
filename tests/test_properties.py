"""Eigenschaftstests (Schicht „Eigenschaften“): Invarianten auf Zufallsmatroiden und Plänen mit festem Seed."""

import random

import numpy as np
import pytest

import mpo_algorithm as A
from mpo_systems import get_net

SEED = 20261116


def _cases(count=40):
    rng = random.Random(SEED)
    out = []
    for n in (3, 4, 5):
        mats = A.small_matroids(n)
        out += [(n, ok, r) for ok, r in rng.sample(mats, min(count // 3, len(mats)))]
    return out


def test_greedy_loest_das_lp_auch_bei_gleichstaenden_und_nullen():
    rng = random.Random(SEED)
    for n, ok, r in _cases():
        for _ in range(4):
            w = [rng.randint(0, 4) for _ in range(n)]
            assert A.lp_max(r, n, w)[0] == pytest.approx(A.greedy(ok, n, w)[1]), (n, w)
            wb = [rng.randint(-3, 4) for _ in range(n)]
            assert A.lp_max(r, n, wb, base=True)[0] == pytest.approx(A.greedy(ok, n, wb, base=True)[1]), (n, wb)


def test_das_greedy_dual_ist_zulaessig_ganzzahlig_und_liegt_auf_einer_kette():
    rng = random.Random(SEED + 1)
    for n, ok, r in _cases():
        for _ in range(4):
            w = [rng.randint(0, 9) for _ in range(n)]
            dual = A.greedy_dual(r, n, w)
            chk = A.dual_check(r, n, w, dual)
            assert chk["feasible"] and chk["integral"] and chk["value"] == A.greedy(ok, n, w)[1]
            flats = [f for f, _ in dual]
            assert all(a & ~b == 0 for a, b in zip(flats, flats[1:]))          # jede Hülle liegt in der nächsten
            assert all(y > 0 for _, y in dual) and len(dual) <= n


def test_umbenennen_der_elemente_aendert_ecken_und_facettenzahl_nicht():
    rng = random.Random(SEED + 2)
    for n, ok, r in _cases(15):
        perm = list(range(n))
        rng.shuffle(perm)
        moved = np.zeros(1 << n, dtype=bool)
        for m in range(1 << n):
            moved[sum(1 << perm[e] for e in range(n) if m >> e & 1)] = ok[m]
        r2 = A.rank_table(moved, n)
        f1, f2 = A.facets(ok, r, n), A.facets(moved, r2, n)
        assert (len(f1["nn"]), len(f1["rank"]), f1["dim"]) == (len(f2["nn"]), len(f2["rank"]), f2["dim"])
        assert len(A.polytope_vertices(ok, r, n, False)) == len(A.polytope_vertices(moved, r2, n, False))
        assert len(A.polytope_edges(ok, r, n, True)) == len(A.polytope_edges(moved, r2, n, True))


def test_der_schnitt_mit_dem_freien_matroid_aendert_das_polytop_nicht():
    for n, ok, r in _cases(12):
        free = np.ones(1 << n, dtype=bool)
        assert A.vertices([ok, free], n) == A.vertices([ok], n)


def test_jede_ecke_erfuellt_jede_rangungleichung_und_basen_haben_rang_r():
    for n, ok, r in _cases(20):
        full = (1 << n) - 1
        for v in A.polytope_vertices(ok, r, n, False):
            assert all(A.popcount(v & s) <= r[s] for s in range(1, 1 << n))
        for b in A.polytope_vertices(ok, r, n, True):
            assert A.popcount(b) == r[full]


def test_facetten_sind_hoechstens_so_viele_wie_ungleichungen_und_die_regel_gilt():
    for n, ok, r in _cases(25):
        f = A.facets(ok, r, n)
        flats, conn = A.flats_of(ok, r, n)
        assert len(f["nn"]) + len(f["rank"]) <= f["total"]
        assert set(f["rank"]) == set(conn) and len(f["nn"]) == len(A.nonloops(ok, n))


def test_schnittebenenlauf_waechst_und_endet_beim_kleinsten_spannbaum():
    for n, seed in [(6, 9), (6, 12), (7, 8), (7, 3), (8, 9), (8, 0)]:
        net = get_net("plan", n, seed)
        opt, _ = A.kruskal(net.n, net.edges, net.costs)
        rounds = A.cutting_plane(net.n, net.edges, net.costs)
        values = [r["value"] for r in rounds]
        assert values == sorted(values) and values[-1] == pytest.approx(opt) and values[0] < opt - 1e-6, (n, seed)
        assert rounds[-1]["violation"] is None and all(r["violation"] is not None for r in rounds[:-1])
        assert all(r["violation"][0] > 0 for r in rounds[:-1])


def test_die_formulierungen_sind_geordnet_schnitt_schwaecher_als_partition_und_rang():
    for n, seed in [(6, 3), (7, 2), (7, 8)]:
        net = get_net("plan", n, seed)
        cut = A.tree_lp(net.n, net.edges, net.costs, "cut")[0]
        part = A.tree_lp(net.n, net.edges, net.costs, "partition")[0]
        rank = A.tree_lp(net.n, net.edges, net.costs, "rank")[0]
        assert cut <= part + 1e-9 and part == pytest.approx(rank)


def test_trennung_ueber_knotenmengen_und_kantenmengen_gleich_beim_wald():
    from mpo_systems import forest_rank
    rng = random.Random(SEED + 3)
    net = get_net("plan", 6, 4)
    r = forest_rank("plan", 6, 4)
    for _ in range(60):
        x = np.array([rng.randint(0, 8) / 8 for _ in range(net.m)])
        by_edges = A.separate(r, net.m, x)[0] < -1e-9
        assert by_edges == (A.violated_set(net.n, net.edges, x) is not None)
