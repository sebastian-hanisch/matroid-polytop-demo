"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jedes Preset zeigt den Effekt, den sein Hilfetext verspricht."""

import mpo_constants as C
import mpo_evaluation as ev
import mpo_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX
        assert preset["net"] in C.NETS and preset["form"] in C.FORMS and preset["mat"] in C.MATROIDS


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    d = ev.Settings()
    assert [P.SETTING_SPECS[key].default for key in ("n_slider", "seed_input", "net_select", "form_select", "mat_select")] == [d.n, d.seed, d.net, d.form, d.mat]


def test_setting_specs_cover_every_preset_key_and_have_valid_defaults():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for spec in P.SETTING_SPECS.values():
        assert spec.choices is None or (spec.default in spec.choices and spec.lo in spec.choices and spec.hi in spec.choices)


def test_no_single_regler_change_of_the_default_lands_on_another_preset():
    """Das Layout setzt jeden Regler auf seinen Höchstwert (oder Tiefstwert): das darf kein Preset treffen, sonst bliebe ein Preset markiert."""
    default = dict(C.PRESETS["Standardfall (Voreinstellung)"])
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        for value in (spec.hi, spec.lo):
            if value == default[key]:
                continue                                  # das Layout setzt dann den anderen Wert
            variant = {**default, key: value}
            assert all(variant != preset for preset in C.PRESETS.values()), (state_key, value)


def test_default_preset_has_a_gap_and_one_cutting_plane():
    s = _settings("Standardfall (Voreinstellung)")
    v = ev.lp_view(s)
    assert (ev.net_of(s).n, ev.net_of(s).m, v["opt"]) == (7, 12, 156) and round(v["value"], 6) == 147.5 and len(ev.rounds_view(s)) >= 2


def test_several_rounds_preset_needs_more_than_one_cutting_plane():
    assert len(ev.rounds_view(_settings("Mehrere Runden"))) - 1 >= 2


def test_rank_and_partition_presets_have_no_gap_but_the_cut_formulation_does_on_the_same_plan():
    for name in ("Rangungleichungen", "Partitionen"):
        s = _settings(name)
        assert ev.lp_view(s)["gap"] < 1e-6 and ev.verdict_lp(s, ev.lp_view(s))[0] in ("success", "info"), name
        assert ev.lp_view(ev.Settings(s.n, s.seed, s.net, "cut", s.mat))["gap"] > 1, name


def test_k5_preset_is_the_hand_example():
    s = _settings("Handbeispiel K5")
    v = ev.lp_view(s)
    assert (ev.net_of(s).n, ev.net_of(s).m, v["opt"], v["gap"]) == (5, 10, 5, 0.5) and round(v["value"], 6) == 4.5


def test_octahedron_preset_has_six_vertices_and_twelve_edges():
    pv = ev.poly_view(_settings("Oktaeder").mat)
    assert (len(pv["vertices"]), len(pv["edges"]), pv["mat"]["base"]) == (6, 12, True)
