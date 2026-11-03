"""Orakel (anderer Rechenweg als die Demo): Kanten über die Mittelpunkt-Zerlegung, Facetten über Redundanztests per LP, Kruskal gegen networkx, Zulässigkeit über Konvexkombinationen
aus Zufallsmischungen, Ecken gegen die Aufzählung der unabhängigen Mengen. Die Demo rechnet dagegen mit Qhull, Rangbedingungen an den Ecken und Aufzählung aller Mengen."""

import itertools
import random

import numpy as np
import pytest
from scipy.optimize import linprog

import mpo_algorithm as A
import mpo_constants as C
from mpo_systems import get_net

nx = pytest.importorskip("networkx")
SEED = 20261115


def _points(ok, r, n, base):
    verts = A.polytope_vertices(ok, r, n, base)
    return verts, np.array([A.indicator(v, n) for v in verts])


def _adjacent(points, i, j):
    """i, j sind Nachbarn genau dann, wenn sich der Mittelpunkt nur aus i und j mischen lässt (kein Gewicht auf den übrigen Ecken)."""
    mid = (points[i] + points[j]) / 2
    others = [k for k in range(len(points)) if k not in (i, j)]
    if not others:
        return True
    c = np.zeros(len(points))
    c[others] = -1.0                                             # maximiere das Gewicht auf den übrigen Ecken
    res = linprog(c, A_eq=np.vstack([points.T, np.ones(len(points))]), b_eq=np.append(mid, 1.0), bounds=[(0, None)] * len(points), method="highs")
    return res.status == 0 and -res.fun < 1e-7


def test_kanten_gegen_mittelpunkt_zerlegung_fuer_alle_matroide_bis_4_elemente():
    for n in range(2, 5):
        for ok, r in A.small_matroids(n):
            for base in (False, True):
                verts, pts = _points(ok, r, n, base)
                if len(verts) < 2:
                    continue
                expected = {(verts[i], verts[j]) for i, j in itertools.combinations(range(len(verts)), 2) if _adjacent(pts, i, j)}
                assert set(A.polytope_edges(ok, r, n, base)) == expected, (n, base)


def _constraint_rows(ok, r, n):
    nl = A.nonloops(ok, n)
    rows = [(("nn", e), -np.eye(n)[e], 0.0) for e in nl]
    nlmask = sum(1 << e for e in nl)
    rows += [(("rk", s), A.indicator(s, n), float(r[s])) for s in range(1, 1 << n) if not s & ~nlmask]
    return nl, rows


def test_facetten_gegen_redundanztest_per_lp_fuer_alle_matroide_bis_4_elemente():
    """Eine Ungleichung ist eine Facette, wenn sie nicht überflüssig ist: Lässt man sie weg, ist das Maximum von a·x unter den übrigen größer als die rechte Seite."""
    for n in range(2, 5):
        for ok, r in A.small_matroids(n):
            nl, rows = _constraint_rows(ok, r, n)
            if not nl:
                continue
            fixed = [e for e in range(n) if e not in nl]
            bounds = [(None, None) if e in nl else (0, 0) for e in range(n)]
            facet_keys = set()
            for idx, (key, a, b) in enumerate(rows):
                others = [row for k, row in enumerate(rows) if k != idx]
                res = linprog(-a, A_ub=np.array([row[1] for row in others]), b_ub=np.array([row[2] for row in others]), bounds=bounds, method="highs")
                if res.status == 3 or -res.fun > b + 1e-7:       # unbeschränkt oder verletzt: die Ungleichung schneidet etwas ab
                    facet_keys.add(key)
            f = A.facets(ok, r, n)
            assert facet_keys == {("nn", e) for e in f["nn"]} | {("rk", s) for s in f["rank"]}, (n, fixed)


def test_kruskal_gegen_networkx_und_lp_gegen_kruskal():
    for n, seed in [(6, s) for s in range(8)] + [(7, s) for s in range(5)]:
        net = get_net("plan", n, seed)
        g = nx.Graph()
        for (u, v), c in zip(net.edges, net.costs):
            g.add_edge(u, v, weight=c)
        mst = sum(d["weight"] for _, _, d in nx.minimum_spanning_edges(g, algorithm="kruskal", data=True))
        opt, tree = A.kruskal(net.n, net.edges, net.costs)
        assert opt == mst, (n, seed)
        assert A.tree_lp(net.n, net.edges, net.costs, "rank")[0] == pytest.approx(opt), (n, seed)
        assert A.tree_lp(net.n, net.edges, net.costs, "partition")[0] == pytest.approx(opt), (n, seed)
        assert A.tree_lp(net.n, net.edges, net.costs, "cut")[0] <= opt + 1e-9, (n, seed)


def test_schnitt_lp_loesung_erfuellt_alle_schnitte_und_den_baum_nicht_immer():
    net = get_net("plan", 7, 8)
    value, x = A.tree_lp(net.n, net.edges, net.costs, "cut")
    for sub in range(1 << (net.n - 1)):
        s = 1 | (sub << 1)
        if s != (1 << net.n) - 1:
            assert sum(x[e] for e, (a, b) in enumerate(net.edges) if (s >> a & 1) != (s >> b & 1)) >= 1 - 1e-7
    assert sum(x) == pytest.approx(net.n - 1)
    assert value == pytest.approx(sum(c * xe for c, xe in zip(net.costs, x)))
    assert value < A.kruskal(net.n, net.edges, net.costs)[0] - 1e-6


def test_zulaessigkeit_gegen_zufallsmischungen_und_ueberschreitung():
    rng = random.Random(SEED)
    for n in (3, 4, 5):
        for ok, r in rng.sample(A.small_matroids(n), min(20, len(A.small_matroids(n)))):
            ind = [m for m in range(1 << n) if ok[m]]
            lam = np.array([rng.random() for _ in ind])
            lam /= lam.sum()
            x = sum(l * A.indicator(m, n) for l, m in zip(lam, ind))
            assert A.separate(r, n, x)[0] >= -1e-9                    # eine Mischung unabhängiger Mengen liegt im Polytop
            assert A.in_hull(ok, n, x)
            full = (1 << n) - 1
            if r[full] < n:
                y = np.ones(n)
                assert A.separate(r, n, y)[0] < -1e-9 and not A.in_hull(ok, n, y)    # x = 1 überschreitet den Rang


def test_ecken_gegen_aufzaehlung_fuer_alle_systeme_bis_4_elemente():
    for n in range(2, 5):
        for ok in A.all_systems(n):
            verts = A.vertices([ok], n)
            ind = A.indep_indicators(ok, n)
            assert ind <= verts                                        # jede unabhängige Menge ist eine Ecke
            if A.System("s", n, [bool(t) for t in ok]).exchange_scan()[1] == 0:
                assert verts == ind                                    # bei Matroiden gibt es keine weiteren


def test_zahlen_der_matroide_und_systeme():
    assert [len(A.small_matroids(n)) for n in range(1, 6)] == [2, 5, 16, 68, 406]
    assert [len(A.all_systems(n)) for n in range(1, 6)] == [2, 5, 19, 167, 7580]


def test_bekannte_werte_oktaeder_und_wuerfel():
    mat = A.named_matroid("u24")
    r = A.rank_table(mat["ok"], 4)
    verts = A.polytope_vertices(mat["ok"], r, 4, True)
    assert sorted(verts) == [0b0011, 0b0101, 0b0110, 0b1001, 0b1010, 0b1100]
    free = np.ones(8, dtype=bool)
    assert len(A.vertices([free], 3)) == 8 and len(A.polytope_edges(free, A.rank_table(free, 3), 3)) == 12      # Würfel: 8 Ecken, 12 Kanten
    assert C.K5_COSTS[2] == 0
