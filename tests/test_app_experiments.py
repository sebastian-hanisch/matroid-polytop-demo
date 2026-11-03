"""AppTest: Hauptansicht, Experimente, Spielwiese, Permalink und PDF (DEMO-PLAYBOOK §3, §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import mpo_constants as C
import mpo_evaluation as ev
from mpo_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
PLAY = "plan_7_8_cut"


def _app(params=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (params or {}).items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning) + list(at.error)]


def _click_preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_default_shows_the_gap_the_first_cutting_plane_and_the_metrics():
    at = _app()
    assert [m.value for m in at.metric][:3] == ["156", "147,5", "8,5"] and int(at.metric[3].value) >= 1
    texts = _texts(at)
    assert any("**Schnitte:** Der LP-Wert ist **147,5**, der kleinste Spannbaum kostet **156**" in t for t in texts)
    assert any(t.startswith("Runde 1: Das LP liegt bei **147,5**") and "verletzt die Rangungleichung" in t for t in texts)
    assert any("= kleinster Spannbaum (156)" in t for t in texts)


def test_round_slider_walks_to_the_last_round():
    at = _app()
    last = len(ev.rounds_view(ev.Settings()))
    at.slider(key=f"round_{PLAY}").set_value(last).run()
    assert not at.exception and any(t.startswith(f"Runde {last}: **Keine Rangungleichung** ist mehr verletzt") for t in _texts(at))


def test_main_verdict_matches_each_preset():
    expected = {
        "Standardfall (Voreinstellung)": "Der LP-Wert ist **147,5**",
        "Mehrere Runden": "Der LP-Wert ist **161,5**, der kleinste Spannbaum kostet **166**",
        "Rangungleichungen": "Der LP-Wert **149** ist gleich dem kleinsten Spannbaum, und die Lösung ist **ganzzahlig**",
        "Partitionen": "Der LP-Wert **156** ist gleich dem kleinsten Spannbaum",
        "Handbeispiel K5": "Der LP-Wert ist **4,5**, der kleinste Spannbaum kostet **5**",
        "Oktaeder": "Der LP-Wert ist **147,5**",
    }
    at = _app()
    for name, needle in expected.items():
        _click_preset(at, name)
        assert any(needle in t for t in _texts(at)), name


def test_formulation_selectbox_changes_the_verdict():
    at = _app()
    at.sidebar.selectbox(key="form_select").set_value("rank").run()
    assert not at.exception and any("**Rangungleichungen:** Der LP-Wert **156** ist gleich dem kleinsten Spannbaum" in t for t in _texts(at))
    assert at.sidebar.selectbox(key="form_select").value == "rank"


def test_experiment_one_dual_and_experiment_four_facets_and_five_separation():
    at = _app()
    texts = _texts(at)
    assert any("Greedy wählt **6** Leitungen mit dem Gewicht **138**" in t for t in texts)
    assert any("Das Waldpolytop dieses Netzes hat **4 107** Ungleichungen" in t and "**33** zusammenhängende" in t and "sind nur **45** davon Facetten" in t for t in texts)
    assert any("Die Lösung des Schnitt-LP liegt **nicht** im Waldpolytop" in t and "**4 095** Leitungsmengen" in t and "**120** Knotenmengen" in t for t in texts)


def test_experiment_two_follows_the_matroid_and_the_weights():
    at = _app()
    assert any("**7** Ecken, genau die unabhängigen Mengen" in t for t in _texts(at))
    at.sidebar.selectbox(key="mat_select").set_value("u24").run()
    assert not at.exception and any("**6** Ecken, genau die Basen; die **12** Kanten" in t for t in _texts(at))
    at.number_input(key="w_u24_2").set_value(9).run()
    assert not at.exception and any("Greedy wählt **ac** mit Gewicht **14**" in t for t in _texts(at))     # Gewichte 5, 3, 9, 2: c (9) und a (5)


def test_on_demand_tables_appear_and_stay():
    at = _app()
    assert not any("497" in t for t in _texts(at))
    at.button(key="small_run").click().run()
    assert not at.exception and any("Bei allen **497** Matroiden" in t for t in _texts(at))
    at.button(key="system_run").click().run()
    assert not at.exception and any("Bei **7 276** Nicht-Matroiden" in t and "bei **4 528** trotzdem ganzzahlig" in t for t in _texts(at))
    at.button(key="pair_run").click().run()
    assert not at.exception and any("Bei allen **5 159** geprüften Paaren" in t and "**6** eine gebrochene Ecke" in t for t in _texts(at))
    at.button(key="series_run").click().run()
    assert not at.exception and any("bei 15 %, 25 %, 40 % der 20 Pläne eine Lücke" in t for t in _texts(at))
    _click_preset(at, "Oktaeder")
    assert any("Bei allen **497** Matroiden" in t for t in _texts(at))                 # die Ergebnisse bleiben nach anderen Änderungen


def test_every_net_and_formulation_runs_without_exception_and_has_a_verdict():
    at = _app()
    for net in C.NETS:
        for form in C.FORMS:
            at.sidebar.selectbox(key="net_select").set_value(net).run()
            at.sidebar.selectbox(key="form_select").set_value(form).run()
            assert not at.exception, (net, form, [str(e) for e in at.exception])
            texts = _texts(at)
            assert any("Der LP-Wert" in t for t in texts) and any("Greedy wählt" in t for t in texts) and any("Ungleichungen" in t for t in texts), (net, form)


def test_every_matroid_runs_without_exception():
    at = _app()
    for key in C.MATROIDS:
        at.sidebar.selectbox(key="mat_select").set_value(key).run()
        assert not at.exception, (key, [str(e) for e in at.exception])
        assert any("Ecken, genau die" in t for t in _texts(at)), key


def test_playground_branches():
    at = _app()
    assert any(t == "Wählen Sie Leitungen mit x = 1 oder x = ½." for t in _texts(at))
    at.multiselect(key=f"play_full_{PLAY}").set_value([0, 1, 2]).run()
    assert not at.exception and any(t.startswith("Der Punkt liegt **nicht** im Waldpolytop") or t.startswith("Der Punkt mit x(E) = 3 liegt im **Waldpolytop**") for t in _texts(at))
    at.multiselect(key=f"play_full_{PLAY}").set_value([]).run()
    at.multiselect(key=f"play_half_{PLAY}").set_value([0, 1, 2]).run()
    assert not at.exception and any(t.startswith("Der Punkt mit x(E) = 1,5") for t in _texts(at))


def test_permalink_loads_valid_values_and_ignores_invalid_choices():
    at = _app(dict(n="8", seed="3", net="k5", form="rank", mat="u14"))
    assert at.sidebar.slider(key="n_slider").value == 8 and at.sidebar.number_input(key="seed_input").value == 3
    assert at.sidebar.selectbox(key="net_select").value == "k5" and at.sidebar.selectbox(key="form_select").value == "rank" and at.sidebar.selectbox(key="mat_select").value == "u14"
    bad = _app(dict(n="99", seed="-4", net="gibtsnicht", form="nichts", mat="xyz"))
    assert bad.sidebar.slider(key="n_slider").value == C.N_MAX and bad.sidebar.number_input(key="seed_input").value == 0
    assert bad.sidebar.selectbox(key="net_select").value == "plan" and bad.sidebar.selectbox(key="form_select").value == "cut" and bad.sidebar.selectbox(key="mat_select").value == "u23"


def test_address_line_mirrors_the_settings():
    at = _app(dict(form="partition"))
    assert str(at.query_params["form"]) in ("partition", "['partition']")


def test_pdf_button_makes_a_download():
    at = _app()
    at.button(key="pdf_make").click().run()
    assert not at.exception and "pdf_made" in at.session_state and at.session_state["pdf_made"][1][:4] == b"%PDF"


def test_pdf_builds_for_every_net_and_formulation():
    for net in C.NETS:
        for form in C.FORMS:
            assert build_pdf(ev.Settings(n=6, seed=2, net=net, form=form))[:4] == b"%PDF", (net, form)


def test_extreme_plan_sizes_do_not_raise():
    for n in (C.N_MIN, C.N_MAX):
        for form in C.FORMS:
            at = _app(dict(n=str(n), form=form))
            assert not at.exception, (n, form)
