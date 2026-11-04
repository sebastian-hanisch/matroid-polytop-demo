# Matroid-Polytop – warum das LP ganzzahlig ist – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-matroid-polytop-demo.streamlit.app/)** -->

Zehntes Stück der Reihe **Matroide und Submodularität** (Bereich Kombinatorik) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Demo macht aus dem Matroid einen **Körper**: Die Indikatorvektoren der unabhängigen Mengen spannen das **Unabhängigkeitspolytop** auf, die der Basen das **Basenpolytop**; beschrieben wird es durch die **Rangungleichungen** x(S) ≤ r(S). Seine **Ecken** sind die unabhängigen Mengen (beziehungsweise die Basen), seine **Kanten** (beim Basenpolytop) die Basenaustausche; **Greedy löst das LP** darüber und liefert das **Dual** gratis. Am Leitungsnetz: Der billigste Spannbaum als LP mit der naheliegenden **Schnittformulierung** ist nicht immer ganzzahlig (in der Messreihe hat sie bei 16 von 60 Plänen eine Lücke), mit den Rangungleichungen des Waldes bei keinem der 60 Pläne; ein **Schnittebenenlauf** macht aus der einen die andere.

**Einordnung in die Reihe:** Nachfolger von [matroid-vereinigung-demo](../matroid-vereinigung-demo) (Stück 9), [gewichteter-schnitt-demo](../gewichteter-schnitt-demo) (Stück 8), [matroid-schnitt-demo](../matroid-schnitt-demo) (Stück 7: zwei Matroide), [greedy-optimalitaet-demo](../greedy-optimalitaet-demo) (Stück 5: Greedy genau bei Matroiden optimal) und [matroid-demo](../matroid-demo) (Stück 3: Austauschaxiom). Das Austauschaxiom wird hier Geometrie (Kanten), der Satz aus Stück 5 wird LP-Sprache (Greedy = LP), und der Schnitt zweier Polytope (Stück 7) wird dem von dreien gegenübergestellt. Wie ein LP gelöst wird, erklären die Demos zu Simplex und LP-Dualität (`lp-dualitaet-demo`, `tableau-simplex-demo`); hier ist das LP nur das Messwerkzeug (HiGHS aus scipy).

## Warum dieses Problem

Warum liefert Kruskal einen Spannbaum, obwohl man ein *lineares* Programm hinschreiben könnte, dessen Lösung gebrochen wäre? Weil man die richtigen Ungleichungen hinschreiben kann: die Rangungleichungen. Dann ist jede Ecke des Polytops ein Wald, und ein LP findet immer eine Ecke. Offen ist: Reicht „ganzzahlig“ schon, um Matroide zu kennzeichnen? Gemessen: nein. Und: Was kostet der Weg über die Ungleichungen, wenn man sie nicht alle aufschreiben will? Ein Schnittebenenlauf ergänzt sie bei Bedarf.

## Befunde und Korrekturen gegenüber dem Plan

- **„Ganzzahlig genau dann, wenn Matroid“ ist falsch.** Auch viele Nicht-Matroide haben ein ganzzahliges Rangungleichungs-Polytop (siehe unten). Was bei Nicht-Matroiden bricht, ist die Verbindung zu Greedy; die Demo behauptet die Umkehrung nirgends.
- **Rundenzahlen des Schnittebenenlaufs hängen vom Löser ab.** Bei mehreren optimalen Ecken kann HiGHS auf einem anderen Rechner eine andere liefern; die Tests prüfen deshalb nur Werte, „ganzzahlig ja/nein“ und ein Band für die Rundenzahl, nie die gezeigte gebrochene Ecke.
- **Die App rechnet kleinere Stichproben als die Messung vor dem Bau:** zwei ganze Gewichte je Matroid statt vier, drei Gitterpunkte statt acht, 150 Nicht-Matroide bei n = 5 statt 1 200, 250 Paare statt 1 500, 20 Pläne je Größe statt 40.
- **Facetten werden nur bis 7 Standorte aus den Ecken nachgerechnet** (bei 8 gäbe es 16 397 Ungleichungen und je nach Plan rund 3 900 bis 5 000 Wälder, Plan 8/9: 4 716); bei 8 Standorten zeigt die App nur die Regel.
- **Port 9350;** Repo `matroid-polytop-demo`, Präfix `mpo_`; `networkx` nur in den Tests, `scipy` zur Laufzeit (HiGHS, Qhull).

## Modell

**Polytop:** P(M) = { x ≥ 0 : x(S) ≤ r(S) für alle S }, B(M) = P(M) ∩ { x(E) = r(E) }. **Netz:** der Plan wie in den Stücken davor (n Standorte, Depot A in der Mitte, min(n(n − 1)/2, 2n − 2) mögliche Leitungen mit Kosten nach Entfernung) oder der vollständige Graph K5 mit den Kosten 2, 3, 0, 1, 3, 2, 2, 3, 3, 0 (Kanten in der Reihenfolge 01, 02, 03, 04, 12, 13, 14, 23, 24, 34). **Drei Formulierungen** des Spannbaum-LP (min c·x, x(E) = n − 1, 0 ≤ x ≤ 1): **Schnitte** (x(δ(S)) ≥ 1 für jede Knotenmenge S), **Partitionen** (x(δ(P)) ≥ |P| − 1 für jede Partition P der Knoten), **Rang** (x(E[U]) ≤ |U| − 1 für jede Knotenmenge U, die Rangungleichungen des Waldmatroids). **Kleine Matroide** für die 3D-Ansicht: U(2,3), eine Partition auf drei Elementen, U(2,4) (Oktaeder), U(2,4) mit paralleler Kante, U(1,4) (Tetraeder). Formeln und Beweisskizzen: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Ecken:** Qhull (`vertices`) über die Halbräume x ≥ 0 und x(S) ≤ r(S) (Schlingen bleiben 0); gegen die Aufzählung der unabhängigen Mengen. Die Kanten (`polytope_edges`): zwei Ecken sind benachbart, wenn die Ecken, die auf allen gemeinsam scharfen Ungleichungen liegen, genau diese beiden sind.
- **Greedy und Dual:** `greedy` nach absteigendem Gewicht, `greedy_dual` mit y auf den Hüllen der Präfixmengen (Gewichtsdifferenz zum nächsten Element); `dual_check` prüft Zulässigkeit, Wert und Ganzzahligkeit; der LP-Wert kommt aus `linprog`.
- **Facetten:** Eine Ungleichung ist eine Facette, wenn die auf ihr liegenden Ecken die affine Dimension d − 1 haben (`facets`); gegen die Regel (x_e ≥ 0 und zusammenhängende Flats, `flats_of`).
- **Trennproblem:** `separate` = Minimum von r(S) − x(S) über alle Mengen; beim Wald `violated_set` über Knotenmengen; gegen die LP-Zulässigkeit als Konvexkombination (`in_hull`).
- **Schnittebenenlauf:** `cutting_plane`: Start mit dem Schnitt-LP, stärkste verletzte Rangungleichung (Knotenmenge) ergänzen, neu lösen, bis keine mehr verletzt ist.
- **Alle kleinen Matroide, alle Systeme, alle Paare:** `small_matroid_row`, `system_row`, `pair_row`, `triple_row`; die Zahlen auf Abruf in der App.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und werden dort mit den Funktionen der App nachgerechnet. LP-Werte kommen aus HiGHS (scipy 1.18); die Tests prüfen sie mit einer Toleranz.

| Beispiel | Leitungen | kleinster Spannbaum | Schnitt-LP | Partitions-LP | Rang-LP |
|---|---|---|---|---|---|
| Plan 7/8 („Standardfall“) | 12 | 156 | 147,5 | 156 | 156 |
| Plan 6/9 („Rangungleichungen“) | 10 | 149 | 143,5 | 149 | 149 |
| Plan 8/9 („Mehrere Runden“) | 14 | 166 | 161,5 | 166 | 166 |
| K5 Handbeispiel | 10 | 5 | 4,5 | 5 | 5 |

| Frage | Befund |
|---|---|
| **Ecken, Kanten** (alle Matroide mit 1 bis 5 Elementen: 2, 5, 16, 68, 406; zusammen **497**) | Ecken von P(M) = unabhängige Mengen, Kanten von B(M) = Basenaustausche, Greedy = LP (Wert), Greedy-Dual zulässig, ganzzahlig und vom selben Wert, Facetten = x_e ≥ 0 und zusammenhängende Flats, Trennung = LP-Zulässigkeit: bei **allen 497**. Ecken, Kanten und Facetten sind vollständig geprüft; Greedy = LP, Dual und Trennung je Matroid an zwei ganzen Gewichtsvektoren beziehungsweise drei Testpunkten. |
| **Nicht-Matroide** (alle Systeme mit 3, 4, 5 Elementen: 19, 167, 7 580) | Nicht-Matroide: 3, 99, **7 174**; davon mit **ganzzahligem** Polytop: **3, 91, 4 434**. Ganzzahligkeit kennzeichnet Matroide also **nicht**. In der Stichprobe (alle bis n = 4, 150 bei n = 5; sechs ganze Gewichte 1 bis 9 je System) scheitert Greedy bei mindestens einem der sechs Gewichtsvektoren in 2 von 3, 58 von 99, 94 von 150 Systemen (bei n = 5 eine Stichprobe, in allen 7 174 Nicht-Matroiden rund 61 %); das LP liegt über dem besten unabhängigen Wert (gebrochene Ecke) bei 0, 4, 14. |
| **Schnitt-LP gegen Rang-LP** (20 Pläne je Größe, Seeds 0 bis 19) | Das Schnitt-LP hat bei **3** (6 Standorte), **5** (7) und **8** (8) der 20 Pläne eine **Lücke**, das Partitions-LP und das Rang-LP bei **keinem**. Der Schnittebenenlauf braucht bei diesen Plänen wenige Runden (getestet: höchstens 6). |
| **Dual aus Greedy** | Plan 7/8: **6** Flats mit y > 0, Wert **138**, gleich dem Greedy-Wert und dem LP-Wert; K5: **3** Flats, Wert **11**. |
| **Facetten auf Plänen** | Plan 7/8: **4 107** Ungleichungen, **255** Flats, davon **33** zusammenhängend, **1 316** Wälder, **45** Facetten (12 + 33). Plan 6/9: **1 033**, **93**, **23**, **396**, **33** (10 + 23). K5: **1 033**, **51**, **26**, **291**, **36** (10 + 26). Die Facetten sind genau x_e ≥ 0 und die zusammenhängenden Flats. |
| **Trennproblem** | Eine optimale Lösung des Schnitt-LP des K5-Handbeispiels (x = ½ auf 01, 02, 04, 12 und 1 auf 03, 34) liegt nicht im Waldpolytop: Die Knotenmenge {A, D, E} hat x(E[U]) = **2,5** > \|U\| − 1 = **2**; über alle **1 023** Leitungsmengen ist der kleinste Wert von r(S) − x(S) gleich **−0,5**, über nur **26** Knotenmengen findet man dieselbe Verletzung. |
| **Zwei Polytope, drei Polytope** | Schnitt zweier Matroid-Polytope bei 1 bis 4 Elementen (4, 25, 256, 4 624 Paare) und 250 Paaren mit 5: alle Ecken ganzzahlig und gleich den gemeinsamen unabhängigen Mengen (zusammen **5 159**). Drei Matroide: bei 2 Elementen 0 von **125** Tripeln mit gebrochener Ecke, bei 3 Elementen **6 von 4 096**; das Dreieck aus drei Partitionsmatroiden hat die Ecke (½, ½, ½). |
| **U(2,3) von Hand** | 7 Ecken, 7 Facetten (x_e ≥ 0 dreimal, x_e ≤ 1 dreimal, x(E) ≤ 2); Gewichte (5, 3, 1): Greedy nimmt a und b (Wert 8), Dual y = 2 auf {a}, y = 3 auf E, Wert 2 · 1 + 3 · 2 = 8. U(2,4): Oktaeder mit **6** Ecken und **12** Kanten. |

## Ehrliche Grenzen

- **Ganzzahlig ist nicht gleich Matroid.** Die Demo zeigt das an allen Systemen mit höchstens 5 Elementen; sie beweist nichts über größere.
- **Kleine Grundmengen.** Rangungleichungen und Facetten werden aufgezählt (2^n Mengen, bis 14 Leitungen); bei großen Matroiden braucht man ein Orakel und ein Trennverfahren (submodulare Minimierung, nicht in dieser Reihe vor Stück 15).
- **Totale duale Ganzzahligkeit** (für jeden ganzzahligen Gewichtsvektor eine ganzzahlige Dual-Lösung) ist ein klassischer Satz (Edmonds), hier nicht bewiesen; gemessen ist das Greedy-Dual an Stichproben ganzer Gewichte.
- **Löser.** HiGHS wählt bei mehreren optimalen Ecken eine; auf einem anderen Rechner kann das eine andere sein, der Wert nicht. Die Rundenzahlen sind deshalb nur mit einem Band getestet.
- **Beispiele auf wenigen Plänen.** Lücken und Rundenzahlen gelten für den Plan 7/8, die Presets und die Seeds 0 bis 19, nicht allgemein.
- **Quellen nur als Auszüge** (arXiv 0909.0840 und 0901.3534 für Ecken und Kanten, 0902.1932 und 1701.08483 für Rangungleichungen und Facetten, MIT-Vorlesungsnotizen Lecture 8 für Greedy über dem Basenpolytop, Goemans Vorlesung 10 und 12 für zwei und drei Matroide; Websuche): Dass x_e ≥ 0 für jedes Element ohne Schlinge eine Facette ist, und die Greedy-Dual-Konstruktion sind hier gemessen und nachgerechnet, nicht belegt; als Standardquellen der Sätze gelten Edmonds 1970 und Schrijver, *Combinatorial Optimization*, Kap. 40 bis 42, beide nicht eingesehen.

## Verifikation

- **Kern:** Ecken, Facetten, Greedy, Dual, Kanten, Trennung und das Spannbaum-LP gegen Handrechnung an U(2,3), am Dreieck und am K5-Handbeispiel (`tests/conftest.py`, `tests/test_algorithm.py`); Randfälle: parallele Elemente, Schlingen, Nullmatroid, Gleichstände, Reglergrenzen, alle Zweige der Spielwiese (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_matroid_polytop.py`): Kanten über die Mittelpunkt-Zerlegung (LP) und Facetten über den Redundanztest (LP) auf allen Matroiden bis 4 Elemente; Kruskal gegen `networkx`; Zulässigkeit gegen Zufallsmischungen unabhängiger Mengen; Ecken gegen die Aufzählung; Matroidzahlen 2, 5, 16, 68, 406 und Systemzahlen 2, 5, 19, 167, 7 580; Oktaeder und Würfel.
- **Eigenschaften** (`tests/test_properties.py`): Greedy = LP bei Gleichständen und Nullen; das Dual ist zulässig, ganzzahlig und liegt auf einer Kette; Umbenennen ändert die Zahlen nicht; Schnitt mit dem freien Matroid ändert das Polytop nicht; jede Ecke erfüllt jede Rangungleichung; die Facettenregel; der Schnittebenenlauf wächst und endet beim kleinsten Spannbaum; Schnitt-LP ≤ Partitions-LP = Rang-LP; Trennung über Knotenmengen = über Kantenmengen.
- **Verdikte und Presets:** jeder Zweig und jede Zahl der Verdikte an gesetzten Eingaben; jedes Preset zeigt den versprochenen Effekt; kein einzelner Reglerwechsel trifft ein anderes Preset.
- **Zahlen aus dieser README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), Hauptansicht, Experimente, Spielwiese, Permalink, PDF; Layout (Kopf, Schnellstart, Hervorhebung) und Footer.
- **Umfang:** siehe `pytest --collect-only -q tests`.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Spannbaum-LP mit Schnittebenenlauf, Kernfrage, sechs Experimente (mit 3D-Ansicht), Messreihe, Spielwiese, Grenzen, Formeln |
| `mpo_constants.py` | Reglergrenzen, Netze, Formulierungen, kleine Matroide, K5-Handbeispiel, Farben, Presets |
| `mpo_scenario.py` | Plan: Standorte, mögliche Leitungen, Kosten (wie in den Stücken davor) |
| `mpo_algorithm.py` | Kern: Tabellen, Ecken, Greedy, Dual, Facetten, Kanten, Trennung, Spannbaum-LP, Schnittebenenlauf, Tabellenzeilen |
| `mpo_systems.py` | die Netze, Waldtabelle und Rangfunktion |
| `mpo_evaluation.py` | Kennzahlen, Ansichten der Experimente, Verdikte |
| `mpo_visualization.py` | Netz mit LP-Lösung, 3D-Polytop, Balken |
| `mpo_presets.py` | Permalink, Presets, Zufalls-Seed |
| `mpo_layout.py` | fester Kopf |
| `mpo_pdf_export.py` | PDF des aktuellen Beispiels |
| `tests/` | Kern, Orakel, Eigenschaften, Verdikte, Presets, Claims, Randfälle, Oberfläche, Layout, Footer, Importe |

## Bewusst nicht umgesetzt

- Polytop der Vereinigung (Stück 9), gewichtetes Schnittpolytop (Stück 8), totale duale Ganzzahligkeit als Satz.
- Lovász-Erweiterung, Polymatroide, submodulare Minimierung als Verfahren (Stück 11, 15).
- Ein eigener Simplex: LPs erklären die Demos zu Simplex und LP-Dualität.
- Erklärseite „verständlich erklärt“ und Website-Einbindung (erst mit der vollständigen Linie).

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests -q`. Die CI läuft mit Python 3.12 (`.github/workflows/tests.yml`); die in Streamlit Cloud eingestellte Python-Version ist beim Deploy zu nennen.

Gebaut mit Streamlit, Plotly, numpy, scipy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
