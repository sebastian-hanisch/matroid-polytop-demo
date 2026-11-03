"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 8, 7           # Standorte inklusive Depot (Knoten A); bis 8 (14 mögliche Leitungen: das Partitions-LP hat bei 8 Standorten 4 139 Ungleichungen)
SEED_MAX, DEFAULT_SEED = 999999, 8
HUB_FACTOR = 0.4                            # nur vom Plan-Erzeuger gebraucht (keine Nabe in dieser Demo)
COST_SCALE = 100                            # nur vom Plan-Erzeuger gebraucht
NETS = ("plan", "k5")
NET_NAMES = {"plan": "Leitungsnetz (Plan)", "k5": "K5 mit Handbeispiel-Kosten"}
FORMS = ("cut", "partition", "rank")
FORM_NAMES = {
    "cut": "Schnitte: jeder Schnitt wird überquert",
    "partition": "Partitionen: k Klassen brauchen k − 1 Leitungen dazwischen",
    "rank": "Rangungleichungen: höchstens |U| − 1 Leitungen in U",
}
MATROIDS = ("u23", "teil3", "u24", "u24p", "u14")
MATROID_NAMES = {
    "u23": "U(2,3): höchstens 2 von 3 (Unabhängigkeitspolytop)",
    "teil3": "Partition: a und b zusammen höchstens 1 (Unabhängigkeitspolytop)",
    "u24": "U(2,4): genau 2 von 4 (Basenpolytop: Oktaeder)",
    "u24p": "U(2,4) mit a ∥ b: 2 von 4, nicht {a, b} (Basenpolytop)",
    "u14": "U(1,4): genau 1 von 4 (Basenpolytop: Tetraeder)",
}
ENUM_MAX_N = 5                              # alle Matroide bis so viele Elemente in den Tabellen auf Abruf
SYSTEM_SAMPLE = 150                         # Nicht-Matroide bei n = 5: so viele fürs Gewichtsexperiment
PAIR_SAMPLE = 250                           # Paare von Matroiden bei n = 5
PLAY_SEED = 20261114
SERIES_N = (6, 7, 8)
SERIES_SEEDS = 20
FACET_CHECK_MAX_N = 7                       # Facetten werden nur bis 7 Standorte per Rang der Ecken nachgerechnet (bei 8 gäbe es 16 000 Ungleichungen)

# Handbeispiel K5: Knoten 0 bis 4, Kanten in dieser Reihenfolge, Kosten laut PLAN-10 (Schnitt-LP 4,5 gegen kleinsten Spannbaum 5)
K5_EDGES = ((0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))
K5_COSTS = (2, 3, 0, 1, 3, 2, 2, 3, 3, 0)
K5_POINTS = ((0.5, 0.9), (0.93, 0.6), (0.77, 0.12), (0.23, 0.12), (0.07, 0.6))

COLOR_NODE = "#4c78a8"
COLOR_DEPOT = "#f0a30a"
COLOR_TREE = "#2F6B65"                      # Leitungen mit x = 1
COLOR_HALF = "#d95f02"                      # gebrochene Werte
COLOR_VIOLATED = "#c0392b"                  # verletzte Knotenmenge
COLOR_OTHER = "rgba(150,150,150,0.55)"
COLOR_VERTEX = "#4c78a8"
COLOR_GREEDY = "#c0392b"
COLOR_FACE = "rgba(76,120,168,0.25)"
COLOR_CLASS = ("#4c78a8", "#1b9e77", "#9467bd", "#d95f02", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf")

PRESETS = {
    "Standardfall (Voreinstellung)": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "net": "plan", "form": "cut", "mat": "u23"},
    "Mehrere Runden": {"n": N_MAX, "seed": 9, "net": "plan", "form": "cut", "mat": "u23"},
    "Rangungleichungen": {"n": N_MIN, "seed": 9, "net": "plan", "form": "rank", "mat": "u23"},
    "Partitionen": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "net": "plan", "form": "partition", "mat": "u23"},
    "Handbeispiel K5": {"n": N_MIN, "seed": DEFAULT_SEED, "net": "k5", "form": "cut", "mat": "u23"},
    "Oktaeder": {"n": DEFAULT_N, "seed": DEFAULT_SEED, "net": "plan", "form": "cut", "mat": "u24"},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Das Leitungsnetz (7 Standorte, 12 Leitungen), billigster Spannbaum als LP mit den Schnittbedingungen: Das LP hat eine Lücke, eine ergänzte Rangungleichung schließt sie.",
    "Mehrere Runden": "Ein Plan mit 8 Standorten, bei dem der Schnittebenenlauf mehrere Runden braucht, bis die Lösung ganzzahlig ist.",
    "Rangungleichungen": "Ein Plan mit 6 Standorten, bei dem die Schnittbedingungen eine Lücke haben; die Rangungleichungen des Waldes nicht.",
    "Partitionen": "Dasselbe Netz wie im Standardfall mit den Partitionsbedingungen: Das LP ist ganzzahlig.",
    "Handbeispiel K5": "Der vollständige Graph mit fünf Knoten und den Handbeispiel-Kosten: Schnitt-LP 4,5, kleinster Spannbaum 5, gebrochene Lösung mit halben Kanten.",
    "Oktaeder": "Das Basenpolytop von U(2,4): ein Oktaeder, dessen 6 Ecken die Basen und dessen 12 Kanten die Basenaustausche sind.",
}
