"""Matroid-Polytop - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 10 der Reihe „Matroide und Submodularität“ (Bereich Kombinatorik). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import mpo_constants as C
from mpo_evaluation import (
    Settings,
    dual_rows,
    dual_view,
    edge_values,
    facet_rows,
    facet_view,
    lp_view,
    net_of,
    pair_rows,
    pair_table,
    plan_series,
    play_view,
    poly_greedy,
    poly_view,
    round_text,
    rounds_view,
    sep_view,
    series_table,
    small_rows,
    small_table,
    system_rows,
    system_table,
    triangle,
    triple_rows,
    triple_table,
    verdict_dual,
    verdict_facets,
    verdict_lp,
    verdict_pairs,
    verdict_play,
    verdict_poly,
    verdict_rounds,
    verdict_series,
    verdict_sep,
    verdict_small,
    verdict_system,
    num,
)
from mpo_layout import dunkles_design, kopf_css
from mpo_pdf_export import build_pdf
from mpo_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from mpo_visualization import build_bar_chart, build_net, build_polytope

st.set_page_config(page_title="Matroid-Polytop – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="LP lösen …")
def _lp(settings):
    return lp_view(settings)


@st.cache_data(show_spinner="Schnittebenenlauf …")
def _rounds(settings):
    return rounds_view(settings)


@st.cache_data(show_spinner="Greedy und Dual …")
def _dual(settings):
    return dual_view(settings)


@st.cache_data(show_spinner="Alle Ungleichungen auf Facetten prüfen …")
def _facets(settings):
    return facet_view(settings)


@st.cache_data(show_spinner=False)
def _sep(settings):
    return sep_view(settings)


@st.cache_data(show_spinner=False)
def _play(settings, full, half):
    return play_view(settings, full, half)


@st.cache_data(show_spinner="Alle Matroide bis 5 Elemente prüfen (einige Sekunden) …")
def _small():
    return small_rows()


@st.cache_data(show_spinner="Alle Unabhängigkeitssysteme bis 5 Elemente prüfen (etwa eine halbe Minute) …")
def _systems():
    return system_rows()


@st.cache_data(show_spinner="Paare und Tripel von Polytopen prüfen (einige Sekunden) …")
def _pairs():
    return pair_rows(), triple_rows()


@st.cache_data(show_spinner="Pläne mit 6 bis 8 Standorten durchrechnen …")
def _series():
    return plan_series()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in mpo_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🔷 Matroid-Polytop – warum das LP ganzzahlig ist")
st.markdown(
    """
Bisher war ein Matroid eine Familie von Mengen. Hier wird es ein **Körper**: Die Indikatorvektoren der unabhängigen Mengen spannen das **Unabhängigkeitspolytop** auf, die der Basen das **Basenpolytop**. Beschrieben wird es durch die **Rangungleichungen** x(S) ≤ r(S). Seine **Ecken** sind genau die unabhängigen Mengen (beziehungsweise die Basen), seine **Kanten** (beim Basenpolytop) genau die Basenaustausche, und **Greedy löst das lineare Programm** darüber und liefert das **Dual** gratis. Am Leitungsnetz sieht man den Nutzen: Der billigste Spannbaum als LP mit der naheliegenden Schnittformulierung ist **nicht immer ganzzahlig** (in der Messreihe hat sie bei 16 von 60 Plänen eine Lücke), mit den Rangungleichungen des Waldes bei keinem der 60 Pläne. Aber Vorsicht: **Ganzzahligkeit allein macht noch kein Matroid**, und beim Schnitt von drei Matroiden bricht sie.

Dies ist das **zehnte Stück** der Reihe „Matroide und Submodularität“. Weiter unten: sechs Experimente (🔬, mit einer 3D-Ansicht), eine **Spielwiese**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Wie man lineare Programme löst, steht in den Demos zu Simplex und LP-Dualität; hier ist das LP nur das Messwerkzeug.
"""
)

with st.expander("So hängt es zusammen", expanded=True):
    st.markdown(
        """
1. **Polytop:** P(M) = { x ≥ 0 : x(S) ≤ r(S) für jede Menge S }. Das sind die Punkte, die man als Mischung unabhängiger Mengen schreiben kann. Das **Basenpolytop** B(M) hat zusätzlich x(E) = r(E).
2. **Ecken und Kanten:** Die Ecken von P(M) sind die Indikatorvektoren der unabhängigen Mengen, die von B(M) die der Basen. Zwei Ecken von B(M) sind benachbart genau dann, wenn sich die Basen durch einen **Austausch** unterscheiden (das Austauschaxiom aus Stück 3 als Geometrie).
3. **Greedy löst das LP:** Gewichte absteigend sortieren und jedes Element nehmen, das unabhängig bleibt. Das **Dual** y liegt auf den Hüllen der Präfixmengen, mit den Gewichtsdifferenzen als Werten: ganzzahlig, zulässig, gleicher Wert.
4. **Facetten:** Von den 2^n + n Ungleichungen sind nur wenige nötig: x_e ≥ 0 und x(F) ≤ r(F) für **zusammenhängende Flats** F.
5. **Trennproblem:** Liegt x im Polytop? Man sucht die Menge S mit dem kleinsten r(S) − x(S); ist der Wert negativ, ist die Rangungleichung zu S verletzt. Beim Wald genügt es, über **Knotenmengen** zu suchen. **Schnittebenenlauf:** verletzte Ungleichung ergänzen, neu lösen, wiederholen.
6. **Zwei oder drei Matroide:** Das Polytop des Schnitts zweier Matroide ist ganzzahlig (Stück 7), das dreier nicht.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Netz**")
    net_key = st.selectbox("Netz", C.NETS, key="net_select", format_func=C.NET_NAMES.get,
                           help="Das Leitungsnetz aus den früheren Stücken (hängt von Standorten und Seed ab) oder der vollständige Graph K5 mit den Kosten des Handbeispiels aus dem Plan.")
    n = st.slider("Standorte (mit Depot A, nur Plan)", *bounds("n_slider"), key="n_slider", help="Wie viele Standorte der Plan hat. Bis 8 (14 mögliche Leitungen). K5 hängt nicht davon ab.")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Plan generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Spannbaum-LP**")
    form = st.selectbox("Formulierung", C.FORMS, key="form_select", format_func=C.FORM_NAMES.get,
                        help="Welche Ungleichungen das LP für den billigsten Spannbaum bekommt: Schnittbedingungen (schwach), Partitionsbedingungen oder die Rangungleichungen des Waldes (Matroid-Polytop).")
    st.markdown("**Kleines Matroid (3D-Ansicht)**")
    mat = st.selectbox("Matroid", C.MATROIDS, key="mat_select", format_func=C.MATROID_NAMES.get, help="Welches Matroid in Experiment 2 als Körper gezeigt wird.")

sync_query_params({"n_slider": int(n), "seed_input": int(seed), "net_select": net_key, "form_select": form, "mat_select": mat})

settings = Settings(int(n), int(seed), net_key, form, mat)
net = net_of(settings)
v = _lp(settings)
rounds = _rounds(settings)
play_id = f"{net_key}_{settings.n}_{settings.seed}_{form}"

# --- Spannbaum-LP -------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Der billigste Spannbaum als LP")
st.caption((f"{C.NET_NAMES[net_key]}: {net.n} Standorte, {net.m} Leitungen" if net_key == "plan" else C.NET_NAMES[net_key] + f": {net.n} Standorte, {net.m} Leitungen") + f". Formulierung: {C.FORM_NAMES[form]}.")
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Optimum", num(v["opt"]), help="Kosten des kleinsten Spannbaums nach Kruskal (Stück 1).")
mc2.metric("LP-Wert", num(v["value"]), help="Optimum des LP mit der gewählten Formulierung.")
mc3.metric("Lücke", num(v["gap"]), delta="ganzzahlig" if v["gap"] < 1e-6 else "gebrochen", delta_color="off")
mc4.metric("Ebenen nötig", len(rounds) - 1, help="Wie viele Rangungleichungen man zum Schnitt-LP ergänzen muss, bis die Lösung ein Spannbaum ist.")
if form == "cut":
    r_idx = 0
    if len(rounds) > 1:
        r_idx = st.slider("Runde", 1, len(rounds), 1, key=f"round_{play_id}", help="Welche Runde des Schnittebenenlaufs angezeigt wird: 1 ist das Schnitt-LP, danach kommt je Runde die stärkste verletzte Rangungleichung dazu.") - 1
    shown = rounds[r_idx]
    x_show, violation = shown["x"], shown["violation"]
else:
    r_idx, x_show, violation = 0, v["x"], None
ev = edge_values(net, x_show)
col_a, col_b = st.columns([3, 2])
with col_a:
    st.plotly_chart(
        build_net(net, ev["full"], ev["frac"], ev["text"], node_mark=[a for a in range(net.n) if violation and violation[1] >> a & 1], tree=[e for e in range(net.m) if v["tree"] >> e & 1]),
        width="stretch", key="map_lp",
    )
    st.caption("Blaugrün: Leitungen mit x = 1, orange gepunktet: gebrochene Werte (beschriftet), grau: x = 0. Orange unterlegt: der kleinste Spannbaum. Rot: die Standorte der verletzten Knotenmenge.")
with col_b:
    st.markdown("**Die Werte x der Leitungen**")
    st.dataframe([{"Leitung": net.labels[e], "Kosten": net.costs[e], "x": num(float(x_show[e])), "im kleinsten Baum": "ja" if v["tree"] >> e & 1 else "–"} for e in range(net.m)], hide_index=True, width="stretch")

if st.button("📄 PDF des aktuellen Beispiels erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(settings))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="matroid-polytop.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Warum ist das LP mit Rangungleichungen ganzzahlig?")
kind_v, text_v = verdict_lp(settings, v)
getattr(st, kind_v)(text_v)
if form == "cut":
    kind_v, text_v = round_text(net, rounds, r_idx)
    getattr(st, kind_v)(text_v)
    kind_v, text_v = verdict_rounds(net, v, rounds)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Greedy löst das LP und liefert das Dual")
st.caption("Gewichte w = (größte Kosten + 1) − Kosten: Der schwerste Wald ist der billigste Spannbaum. Greedy nimmt die Leitungen nach Gewicht; das Dual liegt auf den Hüllen der Präfixmengen, mit den Gewichtsdifferenzen als Werten.")
dv = _dual(settings)
st.dataframe(dual_rows(settings, dv), hide_index=True, width="stretch")
kind_v, text_v = verdict_dual(net, dv)
getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 2: Das Polytop als Körper")
st.caption(f"{C.MATROID_NAMES[mat]}. Die Ecken sind die Mengen, die Kanten die Paare mit dem Austausch eines Elements. Gewichte wählen: Greedy und das LP landen in derselben Ecke (rot).")
pv = poly_view(mat)
n_el = pv["mat"]["n"]
wcols = st.columns(n_el)
defaults = [5, 3, 1, 2]
weights = [int(wcols[i].number_input(f"Gewicht {pv['mat']['labels'][i]}", 0, 9, defaults[i], 1, key=f"w_{mat}_{i}")) for i in range(n_el)]
g = poly_greedy(mat, weights)
st.plotly_chart(build_polytope(pv["mat"], pv["vertices"], pv["edges"], greedy_vertex=g["chosen"]), width="stretch", key="poly3d")
st.caption("Ziehen zum Drehen. Beim Basenpolytop mit vier Elementen sind die Achsen x_a, x_b, x_c; x_d ergibt sich aus der Summe.")
kind_v, text_v = verdict_poly(mat, g)
getattr(st, kind_v)(text_v)
if st.button("📊 Alle Matroide bis 5 Elemente prüfen", key="small_run"):
    st.session_state["small_done"] = True
if st.session_state.get("small_done"):
    rows = _small()
    st.dataframe(small_table(rows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_small(rows)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 3: Und wenn es kein Matroid ist?")
st.caption("Alle Unabhängigkeitssysteme mit 3 bis 5 Elementen: Ist das Polytop der Rangungleichungen ganzzahlig, und was machen Greedy und LP bei Nicht-Matroiden?")
if st.button("📊 Alle Unabhängigkeitssysteme bis 5 Elemente prüfen", key="system_run"):
    st.session_state["system_done"] = True
if st.session_state.get("system_done"):
    srows = _systems()
    st.dataframe(system_table(srows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_system(srows)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 4: Welche Rangungleichungen zählen?")
st.caption("Das Waldpolytop dieses Netzes: Wie viele der Ungleichungen sind nötig (Facetten), und welche?")
fv = _facets(settings)
kind_v, text_v = verdict_facets(net, fv)
getattr(st, kind_v)(text_v)
st.markdown("**Die zusammenhängenden Flats** (zu ihnen gehört je eine Rangungleichung, die eine Facette ist)")
st.dataframe(facet_rows(settings, fv), hide_index=True, width="stretch")

st.subheader("🔬 Experiment 5: Das Trennproblem")
st.caption("Die Lösung des Schnitt-LP: Liegt sie im Waldpolytop? Gesucht ist die Menge mit dem kleinsten r(S) − x(S), einmal über alle Leitungsmengen, einmal nur über Knotenmengen.")
sv = _sep(settings)
kind_v, text_v = verdict_sep(net, sv)
getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 6: Zwei Polytope, drei Polytope")
st.caption("Der Schnitt der Polytope zweier Matroide (Stück 7) und dreier Matroide. Dazu das kleinste Gegenbeispiel: drei Partitionsmatroide auf a, b, c, bei denen je ein Paar abhängig ist.")
tri = triangle()
st.markdown(f"**Dreieck:** gemeinsam unabhängig sind nur ∅, a, b, c; das Polytop des Schnitts hat zusätzlich die Ecke **({', '.join(num(t) for t in tri['fractional'][0])})**.")
if st.button("📊 Alle Paare und Tripel kleiner Matroide prüfen", key="pair_run"):
    st.session_state["pair_done"] = True
if st.session_state.get("pair_done"):
    prows, trows = _pairs()
    st.dataframe(pair_table(prows), hide_index=True, width="stretch")
    st.dataframe(triple_table(trows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_pairs(prows, trows)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Messreihe: Pläne mit 6 bis 8 Standorten")
st.caption("20 Pläne je Größe (Seeds 0 bis 19): Wie oft hat das Schnitt-LP eine Lücke, und wie oft die beiden anderen Formulierungen?")
if st.button("📊 Messreihe über 20 Pläne je Größe", key="series_run"):
    st.session_state["series_done"] = True
if st.session_state.get("series_done"):
    mrows = _series()
    st.dataframe(series_table(mrows), hide_index=True, width="stretch")
    st.plotly_chart(
        build_bar_chart([f"{r['n']} Standorte" for r in mrows], [100.0 * r["cut_gap"] / r["plans"] for r in mrows], [C.COLOR_HALF] * len(mrows), "Plangröße", "Pläne mit Lücke (%)", "%{x}: %{y:.0f} %"),
        width="stretch", key="series_chart",
    )
    kind_v, text_v = verdict_series(mrows)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🛠️ Spielwiese: Ein eigener Punkt im Waldpolytop?")
st.caption("Wählen Sie Leitungen mit x = 1 und mit x = ½ (alle anderen haben x = 0). Die App sagt, ob der Punkt im Waldpolytop liegt, sonst nennt sie die stärkste verletzte Knotenmenge. Ein Kreis aus Leitungen mit x = 1 ist nie im Polytop, ein Kreis mit x = ½ schon.")
full = st.multiselect("Leitungen mit x = 1", list(range(net.m)), default=[], key=f"play_full_{play_id}", format_func=lambda e: net.labels[e])
half = st.multiselect("Leitungen mit x = ½", [e for e in range(net.m) if e not in full], default=[], key=f"play_half_{play_id}", format_func=lambda e: net.labels[e])
pvw = _play(settings, tuple(sorted(full)), tuple(sorted(half)))
kind_v, text_v = verdict_play(settings, pvw)
getattr(st, kind_v)(text_v)
if full or half:
    pe = edge_values(net, pvw["x"])
    mark = [a for a in range(net.n) if pvw["node"] and pvw["node"][1] >> a & 1]
    st.plotly_chart(build_net(net, pe["full"], pe["frac"], pe["text"], node_mark=mark, height=330), width="stretch", key="map_play")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist (wer setzt an) |
|---|---|
| **Ganzzahlig heißt Matroid** | Stimmt nicht: Auch viele Nicht-Matroide haben ein ganzzahliges Rangungleichungs-Polytop (Experiment 3). Was bei ihnen bricht, ist die Verbindung zu Greedy: Greedy kann dann unter dem LP liegen (für passende Gewichte), bei manchen hat das LP sogar eine gebrochene Ecke. **(Stück 5 zeigt die Mengen-Seite)** |
| **Zwei Matroide** | Bei drei Matroiden hat der Schnitt der Polytope schon bei drei Elementen eine gebrochene Ecke (Experiment 6). **(nicht in dieser Reihe)** |
| **Kleine Grundmengen** | Alle Rangungleichungen und Facetten werden aufgezählt (2^n Mengen, bis 14 Leitungen); die Trennung über alle Mengen ist submodulare Minimierung. Bei großen Matroiden braucht man ein Orakel und ein Trennverfahren. **(Stück 15, gelb)** |
| **Gewichte** | Das Dual ist für ganze Gewichte gemessen. Dass es für **jeden** ganzzahligen Gewichtsvektor eine ganzzahlige Dual-Lösung gibt (totale duale Ganzzahligkeit), ist ein klassischer Satz (Edmonds), hier nicht bewiesen; gemessen ist das Greedy-Dual an Stichproben ganzer Gewichte. **(nicht in dieser Reihe)** |
| **Das LP ist ein Messwerkzeug** | HiGHS löst die LPs; bei mehreren optimalen Ecken kann die gezeigte gebrochene Lösung auf einem anderen Rechner eine andere sein, der Wert nicht. Wie ein LP gelöst wird, erklären die Demos zu Simplex und LP-Dualität. **(Querverweis)** |
| **Das Beispiel ist klein und zufällig** | Lücken und Rundenzahlen gelten für den gezeigten Plan und die Seeds der Messreihe (0 bis 19), nicht allgemein; die Facettenregel ist bei 7 Standorten nachgerechnet, bei 8 nur als Regel angegeben. **(nicht allgemein)** |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** ein Matroid $M = (E, \mathcal{I})$ mit Rangfunktion $r$ und Gewichte $w \in \mathbb{R}^E$.

| Symbol | Bedeutung |
|---|---|
| $P(M)$ | $\{x \in \mathbb{R}^E_{\ge 0} : x(S) \le r(S)\ \forall S \subseteq E\}$ |
| $B(M)$ | $P(M) \cap \{x(E) = r(E)\}$ |
| $\chi^I$ | Indikatorvektor der Menge $I$ |

**Ecken, Kanten.** Die Ecken von $P(M)$ sind die $\chi^I$ mit $I \in \mathcal{I}$, die von $B(M)$ die $\chi^B$ der Basen; zwei Basen sind genau dann durch eine Kante verbunden, wenn $\lvert B \triangle B' \rvert = 2$.

**Greedy und Dual.** Für $w \ge 0$ sei $e_1, \dots, e_n$ nach $w$ absteigend sortiert, $S_i = \{e_1, \dots, e_i\}$, $w_{n+1} = 0$. Greedy liefert $I$ mit $w(I) = \max\{w^\top x : x \in P(M)\}$. Das Dual
$$\min \sum_S r(S)\, y_S \quad \text{s.t.} \quad \sum_{S \ni e} y_S \ge w_e,\ y \ge 0$$
hat die zulässige Lösung $y_{\operatorname{cl}(S_i)} = w_{e_i} - w_{e_{i+1}}$ (Beträge auf gleichen Hüllen addiert); sie ist für ganze $w$ ganzzahlig und hat den Wert $\sum_i (w_{e_i} - w_{e_{i+1}})\, r(S_i) = w(I)$.

**Facetten.** $x_e \ge 0$ ist für jedes Element ohne Schlinge eine Facette (hier gemessen, nicht belegt); $x(F) \le r(F)$ ist genau dann eine, wenn $F$ ein zusammenhängendes Flat ist (Quelle: Auszug, siehe unten).

**Trennproblem.** $x \in P(M)$ genau dann, wenn $\min_S \big( r(S) - x(S) \big) \ge 0$ und $x \ge 0$. Beim Waldmatroid genügt $\max_U \big( x(E[U]) - (\lvert U \rvert - 1) \big) \le 0$ über Knotenmengen $U$ (gemessen: gleiche Entscheidung wie über Kantenmengen).

**Spannbaum-LP.** $\min c^\top x$ mit $x(E) = n - 1$, $0 \le x \le 1$ und (Schnitt) $x(\delta(S)) \ge 1$ für jede Knotenmenge $S$, oder (Partition) $x(\delta(\mathcal{P})) \ge \lvert\mathcal{P}\rvert - 1$, oder (Rang) $x(E[U]) \le \lvert U \rvert - 1$. Die letzten beiden hatten bei allen Plänen der Messreihe keine Lücke; die Schnittbedingung wird durch $x_e = \tfrac12$ auf einem Kreis verletzt zugelassen.

**Literatur.** Die Beschreibung durch Rangungleichungen und die Facettenaussage (Rangungleichung genau für abgeschlossene, zusammenhängende Mengen) stehen in Auszügen zu Edmonds' Matroid-Polytop (arXiv 0902.1932, 1701.08483), Ecken und Kanten des Basenpolytops in arXiv 0909.0840 und 0901.3534, Greedy für lineare Optimierung über Basenpolytope in MIT-Vorlesungsnotizen zu Lernen mit kombinatorischer Struktur (Lecture 8), ganzzahliger Schnitt zweier Matroid-Polytope und gebrochener Schnitt dreier in Goemans' Vorlesung 10 und 12 (MIT 18.438; Quelle: Websuche, Auszüge, nicht gegen die Primärtexte geprüft; Standardquellen für die Sätze: Edmonds 1970 und Schrijver, *Combinatorial Optimization*, Kap. 40 bis 42, beide nicht eingesehen). Die Dual-Konstruktion aus der Greedy-Reihenfolge und die Zahlen sind hier nachgerechnet.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Matroide: vom Spannbaum zur Verfahrenswahl](https://sebastianhanisch.net/konzepte-matroide.html)."
)
