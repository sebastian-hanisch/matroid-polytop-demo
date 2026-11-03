"""Verdikte (reine Funktionen in mpo_evaluation.py) an handgesetzten Werten: jeder Zweig, jede Zahl im Text (DEMO-PLAYBOOK §4).
LP-Lösungen mit mehreren optimalen Ecken können je nach Löser-Version verschieden ausfallen; deshalb bekommen die Verdikte hier gesetzte Eingaben, und nur die Werte der LPs stehen fest."""

import numpy as np

import mpo_algorithm as A
import mpo_constants as C
import mpo_evaluation as ev
from mpo_systems import forest_rank

K5 = ev.Settings(**C.PRESETS["Handbeispiel K5"])
HAND_X = np.array([0.5, 0.5, 1.0, 0.5, 0.5, 0.0, 0.0, 0.0, 0.0, 1.0])          # Schnitt-LP-Lösung aus PLAN-10: ½ auf 01, 02, 04, 12, 1 auf 03, 34


def _v(value, opt, x, fractional):
    return {"value": value, "opt": opt, "gap": opt - value, "x": np.array(x), "fractional": fractional, "tree": 0}


# --- Hauptansicht --------------------------------------------------------------------------------------------------------------------------


def test_lp_verdict_with_a_gap_names_value_cost_and_the_fractional_edges():
    kind, text = ev.verdict_lp(K5, _v(4.5, 5, HAND_X, True))
    assert kind == "warning" and text.startswith("**Schnitte:** Der LP-Wert ist **4,5**, der kleinste Spannbaum kostet **5**: eine **Lücke** von 0,5.")
    assert "**gebrochen** (4 Leitungen mit Werten zwischen 0 und 1)" in text


def test_lp_verdict_integral_fractional_tie_and_impossible():
    tree = [1, 1, 1, 0, 0, 0, 0, 0, 0, 1]
    kind, text = ev.verdict_lp(ev.Settings(form="rank"), _v(5, 5, tree, False))
    assert kind == "success" and text == "**Rangungleichungen:** Der LP-Wert **5** ist gleich dem kleinsten Spannbaum, und die Lösung ist **ganzzahlig**: ein Spannbaum."
    kind, text = ev.verdict_lp(K5, _v(5, 5, HAND_X, True))
    assert kind == "info" and "gebrochen (mehrere optimale Ecken)" in text
    assert ev.verdict_lp(K5, _v(5.5, 5, tree, False))[0] == "error"


def test_round_text_names_the_violated_set_and_the_final_round():
    net = ev.net_of(K5)
    rounds = ({"x": HAND_X, "value": 4.5, "violation": (0.5, 0b11001)}, {"x": np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 1.0]), "value": 5.0, "violation": None})
    kind, text = ev.round_text(net, rounds, 0)
    assert kind == "info" and text.startswith("Runde 1: Das LP liegt bei **4,5**. Die Knotenmenge **{A, D, E}** verletzt die Rangungleichung: x(E[U]) = **2,5** > |U| − 1 = **2**")
    assert "(3 Leitungen in U, Verletzung 0,5)" in text
    kind, text = ev.round_text(net, rounds, 1)
    assert kind == "success" and text == "Runde 2: **Keine Rangungleichung** ist mehr verletzt. Das LP liegt bei **5**, nach 1 ergänzten Ungleichungen."
    one = ({"x": rounds[1]["x"], "value": 5.0, "violation": None},)
    assert "die Schnittbedingungen allein reichen hier schon" in ev.round_text(net, one, 0)[1]


def test_rounds_verdict_counts_the_added_inequalities_and_checks_the_end():
    v = _v(4.5, 5, HAND_X, True)
    two = ({"x": HAND_X, "value": 4.5, "violation": (0.5, 1)}, {"x": HAND_X, "value": 5.0, "violation": None})
    kind, text = ev.verdict_rounds(None, v, two)
    assert kind == "success" and text == "Start: Schnitt-LP **4,5**; nach **1** ergänzten Rangungleichungen: **5** = kleinster Spannbaum (5)."
    assert ev.verdict_rounds(None, v, (two[1],))[1] == "Das Schnitt-LP liegt schon bei **5**, dem kleinsten Spannbaum: Es ist keine Rangungleichung zu ergänzen."
    assert ev.verdict_rounds(None, v, (two[0],))[0] == "error"


def test_edge_values_split_full_fractional_and_zero():
    ev_ = ev.edge_values(ev.net_of(K5), HAND_X)
    assert ev_["full"] == [2, 9] and ev_["frac"] == [0, 1, 3, 4] and ev_["text"] == {0: "0,5", 1: "0,5", 3: "0,5", 4: "0,5"}


def test_the_real_lp_values_of_the_k5_example():
    v = ev.lp_view(K5)
    assert round(v["value"], 6) == 4.5 and v["opt"] == 5 and v["gap"] == 0.5 and v["fractional"]
    assert ev.verdict_lp(K5, v)[0] == "warning"
    rounds = ev.rounds_view(K5)
    assert round(rounds[0]["value"], 6) == 4.5 and rounds[-1]["violation"] is None and round(rounds[-1]["value"], 6) == 5.0


# --- Experimente ---------------------------------------------------------------------------------------------------------------------------


def test_dual_verdict_and_rows_at_the_k5_example():
    net = ev.net_of(K5)
    d = ev.dual_view(K5)
    kind, text = ev.verdict_dual(net, d)
    assert kind == "success" and text.startswith("Greedy wählt **4** Leitungen mit dem Gewicht **11**; das ist derselbe Baum wie bei Kruskal.")
    assert f"Das Dual hat **{len(d['dual'])}** Flats mit y > 0 (eine Kette), ist zulässig und **ganzzahlig**; sein Wert **11** ist gleich dem Greedy-Wert und gleich dem LP-Wert (11)." in text
    rows = ev.dual_rows(K5, d)
    assert [r["Leitungen"] for r in rows] == sorted(r["Leitungen"] for r in rows) and sum(r["y"] * r["Rang"] for r in rows) == 11
    broken = {**d, "value": d["value"] - 1}
    assert ev.verdict_dual(net, broken)[0] == "error"


def test_polytope_verdict_for_the_octahedron_and_the_cube_cut():
    g = ev.poly_greedy("u24", [5, 3, 1, 2])
    kind, text = ev.verdict_poly("u24", g)
    assert kind == "success" and "**6** Ecken, genau die Basen; die **12** Kanten sind genau die **12** Paare von Basen" in text and "Greedy wählt **ab** mit Gewicht **8**" in text
    assert ev.verdict_poly("u24", {**g, "lp": 9.0})[0] == "error"
    kind, text = ev.verdict_poly("u23", ev.poly_greedy("u23", [5, 3, 1]))
    assert "**7** Ecken, genau die unabhängigen Mengen; es hat **12** Kanten" in text and "Greedy wählt **ab** mit Gewicht **8**" in text


def test_small_system_pair_and_series_verdicts():
    rows = ({"n": 1, "matroids": 2, "vertices": 2, "edges": 2, "greedy": 2, "dual": 2, "facets": 2, "separation": 2},
            {"n": 2, "matroids": 5, "vertices": 5, "edges": 5, "greedy": 5, "dual": 5, "facets": 5, "separation": 5})
    kind, text = ev.verdict_small(rows)
    assert kind == "success" and text.startswith("Bei allen **7** Matroiden mit höchstens 2 Elementen") and "(**0 Abweichungen**)" in text
    bad = (rows[0], {**rows[1], "greedy": 4})
    assert ev.verdict_small(bad) == ("error", "Bei 1 Prüfungen gilt eine Aussage nicht. Das darf nicht sein: Rechenfehler.")
    srows = ({"n": 4, "systems": 167, "matroids": 68, "matroids_integral": 68, "non": 99, "non_integral": 91, "sample": 99, "greedy_fail": 58, "lp_gap": 4},)
    kind, text = ev.verdict_system(srows)
    assert kind == "info" and "Bei **99** Nicht-Matroiden (n = 4 bis 4) ist das Polytop der Rangungleichungen bei **91** trotzdem ganzzahlig" in text and "scheitert Greedy bei **58**" in text and "bei **4** (gebrochene Ecke)" in text
    assert ev.verdict_system(({**srows[0], "matroids_integral": 67},))[0] == "error"
    prow = ({"n": 3, "pairs": 256, "integral": 256, "common": 256},)
    trow = ({"n": 3, "triples": 4096, "fractional": 6},)
    kind, text = ev.verdict_pairs(prow, trow)
    assert kind == "success" and "Bei allen **256** geprüften Paaren" in text and "Von **4 096** Tripeln mit 3 Elementen haben **6** eine gebrochene Ecke, zum Beispiel (0,5, 0,5, 0,5)" in text
    assert ev.verdict_pairs(({**prow[0], "common": 255},), trow)[0] == "error"
    mrows = tuple({"n": n, "plans": 20, "cut_gap": gap, "partition_gap": 0, "rank_gap": 0, "rounds_max": rm} for n, gap, rm in ((6, 3, 1), (7, 5, 2), (8, 8, 4)))
    kind, text = ev.verdict_series(mrows)
    assert kind == "info" and "hat das Schnitt-LP bei 15 %, 25 %, 40 % der 20 Pläne eine Lücke" in text and "höchstens 4 Runden" in text
    assert ev.verdict_series(({**mrows[0], "rank_gap": 1},) + mrows[1:])[0] == "error"


def test_facet_verdict_counts_at_the_k5_example_and_the_unchecked_case():
    net = ev.net_of(K5)
    v = ev.facet_view(K5)
    kind, text = ev.verdict_facets(net, v)
    assert kind == "success" and "**1 033** Ungleichungen" in text and "**51** Flats, davon **26** zusammenhängende" in text and "aus den **291** Ecken (Wäldern) sind nur **36** davon Facetten: **10** der Form x_e ≥ 0 und **26** Rangungleichungen" in text
    assert "Alle übrigen **997** Ungleichungen sind überflüssig." in text
    assert ev.verdict_facets(net, {**v, "rule": False})[0] == "error"
    kind, text = ev.verdict_facets(ev.net_of(ev.Settings(8, 8)), {"flats": 755, "conn": list(range(45)), "ineq": 16397, "checked": False, "forests": 4716})
    assert kind == "info" and "Bei 8 Standorten werden die Facetten nicht aus den Ecken nachgerechnet" in text and "liefert 59" in text


def test_separation_verdict_with_the_hand_point_and_the_inside_case():
    net = ev.net_of(K5)
    r = forest_rank("k5", 0, 0)
    by_edges, arg = A.separate(r, net.m, HAND_X)
    v = {"x": HAND_X, "by_edges": by_edges, "edge_set": arg, "node": A.violated_set(net.n, net.edges, HAND_X)}
    kind, text = ev.verdict_sep(net, v)
    assert kind == "warning" and "Über alle **1 023** Leitungsmengen ist der kleinste Wert von r(S) − x(S) gleich **−0,5** (bei 3 Leitungen)" in text
    assert "über nur **26** Knotenmengen" in text and "U = {A, D, E} mit 3 Leitungen, x(E[U]) = 2,5 > 2" in text
    tree = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 1.0])
    ok = {"x": tree, "by_edges": A.separate(r, net.m, tree)[0], "edge_set": 0, "node": A.violated_set(net.n, net.edges, tree)}
    kind, text = ev.verdict_sep(net, ok)
    assert kind == "success" and "Keine der **1 023** Leitungsmengen und keine der **26** Knotenmengen" in text
    assert ev.verdict_sep(net, {**ok, "node": (0.5, 3)})[0] == "error"


def test_play_verdict_all_branches():
    s = K5
    assert ev.verdict_play(s, ev.play_view(s, (), ())) == ("info", "Wählen Sie Leitungen mit x = 1 oder x = ½.")
    kind, text = ev.verdict_play(s, ev.play_view(s, (2, 3, 9), ()))                 # Dreieck A, D, E mit x = 1
    assert kind == "warning" and "Die Knotenmenge {A, D, E} hat x(E[U]) = **3** > |U| − 1 = **2** (3 Leitungen in U)." in text
    kind, text = ev.verdict_play(s, ev.play_view(s, (), (2, 3, 9)))                 # dasselbe Dreieck mit x = ½
    assert kind == "success" and text.startswith("Der Punkt mit x(E) = 1,5 liegt im **Waldpolytop**")
    kind, text = ev.verdict_play(s, ev.play_view(s, (0, 1, 2, 9), ()))              # Spannbaum
    assert kind == "success" and "x(E) = 4" in text
    assert ev.play_view(s, (2,), (2,))["x"][2] == 1.0                              # x = 1 gewinnt gegen x = ½
