"""Jede Zahl der README („Befunde“) wird hier mit den Funktionen der App nachgerechnet (DEMO-PLAYBOOK §4)."""

from pathlib import Path

import numpy as np
import pytest

import mpo_algorithm as A
import mpo_constants as C
import mpo_evaluation as ev
from mpo_systems import forest_rank, get_net

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")

EXAMPLES = {   # Zeile der README -> (Einstellungen, Leitungen, kleinster Spannbaum, Schnitt-LP, Partitions-LP, Rang-LP)
    "Plan 7/8 („Standardfall“)": (ev.Settings(7, 8), 12, 156, 147.5, 156, 156),
    "Plan 6/9 („Rangungleichungen“)": (ev.Settings(6, 9), 10, 149, 143.5, 149, 149),
    "Plan 8/9 („Mehrere Runden“)": (ev.Settings(8, 9), 14, 166, 161.5, 166, 166),
    "K5 Handbeispiel": (ev.Settings(net="k5"), 10, 5, 4.5, 5, 5),
}


def _fmt(x):
    return ev.num(x)


def test_the_example_table():
    for name, (s, m, opt, cut, part, rank) in EXAMPLES.items():
        net = ev.net_of(s)
        assert net.m == m and A.kruskal(net.n, net.edges, net.costs)[0] == opt, name
        values = [A.tree_lp(net.n, net.edges, net.costs, kind)[0] for kind in ("cut", "partition", "rank")]
        assert values == pytest.approx([cut, part, rank], abs=1e-6), name
        row = f"| {name} | {m} | {opt} | {_fmt(cut)} | {_fmt(part)} | {_fmt(rank)} |"
        assert row in README, row


def test_all_small_matroids():
    rows = ev.small_rows()
    assert [r["matroids"] for r in rows] == [2, 5, 16, 68, 406] and sum(r["matroids"] for r in rows) == 497
    for key in ("vertices", "edges", "greedy", "dual", "facets", "separation"):
        assert all(r[key] == r["matroids"] for r in rows), key
    assert "zusammen **497**" in README and "bei **allen 497**" in README


def test_all_independence_systems_up_to_five_elements():
    rows = ev.system_rows()
    assert [(r["n"], r["systems"], r["matroids"], r["matroids_integral"], r["non"], r["non_integral"]) for r in rows] == [
        (3, 19, 16, 16, 3, 3), (4, 167, 68, 68, 99, 91), (5, 7580, 406, 406, 7174, 4434)]
    assert [(r["sample"], r["greedy_fail"], r["lp_gap"]) for r in rows] == [(3, 2, 0), (99, 58, 4), (150, 94, 14)]
    for text in ("(alle Systeme mit 3, 4, 5 Elementen: 19, 167, 7 580)", "Nicht-Matroide: 3, 99, **7 174**", "**3, 91, 4 434**",
                 "scheitert Greedy bei 2 von 3, 58 von 99, 94 von 150", "bei 0, 4, 14"):
        assert text in README, text


def test_the_series_over_twenty_plans():
    rows = ev.plan_series()
    assert [(r["n"], r["plans"], r["cut_gap"], r["partition_gap"], r["rank_gap"]) for r in rows] == [(6, 20, 3, 0, 0), (7, 20, 5, 0, 0), (8, 20, 8, 0, 0)]
    assert all(1 <= r["rounds_max"] <= 6 for r in rows)                      # Rundenzahlen hängen vom Löser ab: nur ein Band
    assert "bei **3** (6 Standorte), **5** (7) und **8** (8) der 20 Pläne eine **Lücke**" in README and "(getestet: höchstens 6)" in README


def test_the_dual():
    d = ev.dual_view(ev.Settings())
    assert (len(d["dual"]), d["value"], d["check"]["value"]) == (6, 138, 138) and round(d["lp"], 6) == 138.0
    k5 = ev.dual_view(ev.Settings(net="k5"))
    assert (len(k5["dual"]), k5["value"], k5["check"]["value"]) == (3, 11, 11) and round(k5["lp"], 6) == 11.0
    assert "**6** Flats mit y > 0, Wert **138**" in README and "K5: **3** Flats, Wert **11**" in README


def test_the_facets_on_plans():
    cases = {"Plan 7/8: **4 107** Ungleichungen, **255** Flats, davon **33** zusammenhängend, **1 316** Wälder, **45** Facetten (12 + 33).": (ev.Settings(7, 8), 4107, 255, 33, 1316, 12, 33),
             "Plan 6/9: **1 033**, **93**, **23**, **396**, **33** (10 + 23).": (ev.Settings(6, 9), 1033, 93, 23, 396, 10, 23),
             "K5: **1 033**, **51**, **26**, **291**, **36** (10 + 26).": (ev.Settings(net="k5"), 1033, 51, 26, 291, 10, 26)}
    for text, (s, ineq, flats, conn, forests, nn, rk) in cases.items():
        f = ev.facet_view(s)
        assert (f["ineq"], f["flats"], len(f["conn"]), f["forests"], f["facets_nn"], f["facets_rk"], f["rule"]) == (ineq, flats, conn, forests, nn, rk, True), s
        assert text in README, text
    assert ev.facet_view(ev.Settings(8, 9))["checked"] is False and ev.facet_view(ev.Settings(8, 9))["ineq"] == 16397 and ev.facet_view(ev.Settings(8, 9))["forests"] == 4716


def test_the_separation_example():
    net = ev.net_of(ev.Settings(net="k5"))
    x = np.array([0.5, 0.5, 1.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 1.0])
    viol = A.violated_set(net.n, net.edges, x)
    assert viol[1] == 0b11001 and sum(x[e] for e in A.inside_edges(net.edges, viol[1])) == 2.5 and A.popcount(viol[1]) - 1 == 2
    by_edges, _ = A.separate(forest_rank("k5", 0, 0), net.m, x)
    assert by_edges == pytest.approx(-0.5) and (1 << net.m) - 1 == 1023 and (1 << net.n) - net.n - 1 == 26
    assert "x(E[U]) = **2,5** > \\|U\\| − 1 = **2**" in README and "**1 023** Leitungsmengen" in README and "gleich **−0,5**" in README and "nur **26** Knotenmengen" in README
    assert round(A.tree_lp(net.n, net.edges, net.costs, "cut")[0], 6) == 4.5                  # der Wert dieser Lösung ist der des Schnitt-LP: 0,5 · (2 + 3 + 1 + 3) + 0 + 0 = 4,5
    assert sum(c * xe for c, xe in zip(net.costs, x)) == pytest.approx(4.5)


def test_pairs_and_triples():
    rows = ev.pair_rows()
    assert [r["pairs"] for r in rows] == [4, 25, 256, 4624, 250] and sum(r["pairs"] for r in rows) == 5159
    assert all(r["integral"] == r["pairs"] == r["common"] for r in rows)
    trows = ev.triple_rows()
    assert [(r["n"], r["triples"], r["fractional"]) for r in trows] == [(2, 125, 0), (3, 4096, 6)]
    tri = ev.triangle()
    assert tri["fractional"] == [(0.5, 0.5, 0.5)] and len(tri["common"]) == 4
    for text in ("(4, 25, 256, 4 624 Paare) und 250 Paaren mit 5", "(zusammen **5 159**)", "0 von **125** Tripeln", "**6 von 4 096**", "(½, ½, ½)"):
        assert text in README, text


def test_u23_by_hand_in_the_readme():
    pv = ev.poly_view("u23")
    assert len(pv["vertices"]) == 7 and len(pv["facets"]["nn"]) + len(pv["facets"]["rank"]) == 7 + 0 and len(pv["facets"]["nn"]) == 3
    assert ev.poly_view("u24")["facets"]["dim"] == 3 and (len(ev.poly_view("u24")["vertices"]), len(ev.poly_view("u24")["edges"])) == (6, 12)
    assert "7 Ecken, 7 Facetten (x_e ≥ 0 dreimal, x_e ≤ 1 dreimal, x(E) ≤ 2)" in README and "Wert 2 · 1 + 3 · 2 = 8" in README
    assert "**6** Ecken und **12** Kanten" in README


def test_plan_sizes_and_k5_costs_in_the_readme():
    assert [get_net("plan", n, 8).m for n in (6, 7, 8)] == [10, 12, 14] and C.K5_COSTS == (2, 3, 0, 1, 3, 2, 2, 3, 3, 0)
    assert "Kosten 2, 3, 0, 1, 3, 2, 2, 3, 3, 0" in README and "bei 8 gäbe es 16 397 Ungleichungen und 4 716 Wälder" in README
