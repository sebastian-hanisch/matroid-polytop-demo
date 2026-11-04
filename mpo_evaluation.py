"""Kennzahlen, Experimente und Verdikte. Alle sichtbaren Zahlen kommen aus diesen Funktionen."""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import mpo_constants as C
from mpo_algorithm import (
    cutting_plane,
    dual_check,
    facets,
    flats_of,
    greedy,
    greedy_dual,
    inside_edges,
    is_fractional,
    kruskal,
    lp_max,
    named_matroid,
    plan_series_row,
    polytope_edges,
    polytope_vertices,
    exchange_pairs,
    popcount,
    rank_table,
    separate,
    small_matroid_row,
    system_row,
    pair_row,
    triple_row,
    tree_lp,
    triangle_example,
    violated_set,
    components,
)
from mpo_systems import forest_rank, forest_table, get_net, node_names


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def num(x: float) -> str:
    """Ganze Zahl ohne, sonst mit bis zu zwei Nachkommastellen (Dezimalkomma)."""
    if abs(x - round(x)) < 1e-9:
        text = str(int(round(x)))
    else:
        text = f"{x:.2f}".rstrip("0").rstrip(".").replace(".", ",")
    return text.replace("-", "−")


def prozent(x: float, digits: int = 1) -> str:
    return de(100.0 * x, digits)


def zahl(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    net: str = "plan"
    form: str = "cut"
    mat: str = "u23"


def net_of(s: Settings):
    return get_net(s.net, s.n, s.seed)


def net_key(s: Settings) -> tuple:
    """Normalisierte Netz-Eingabe (beim festen K5 zählen n und der Seed nicht), damit die Zwischenspeicher nicht doppelt rechnen."""
    return (s.net, s.n, s.seed) if s.net == "plan" else (s.net, 0, 0)


def _edge_names(net, mask: int) -> str:
    return ", ".join(net.labels[e] for e in range(net.m) if mask >> e & 1)


def _plain(x, n: int = 0):
    return np.array([round(float(v), 9) for v in x])


# --- Hauptansicht: Spannbaum-LP und Schnittebenenlauf ------------------------------------------------------------------------------------------


@lru_cache(maxsize=64)
def _lp(key: tuple, form: str) -> dict:
    net = get_net(*key)
    opt, tree = kruskal(net.n, net.edges, net.costs)
    value, x = tree_lp(net.n, net.edges, net.costs, form)
    return {"value": value, "x": _plain(x), "opt": opt, "tree": tree, "gap": opt - value, "fractional": is_fractional(x)}


def lp_view(s: Settings) -> dict:
    return _lp(net_key(s), s.form)


@lru_cache(maxsize=64)
def _rounds(key: tuple) -> tuple:
    net = get_net(*key)
    rounds = cutting_plane(net.n, net.edges, net.costs)
    return tuple({"x": _plain(r["x"]), "value": r["value"], "violation": r["violation"]} for r in rounds)


def rounds_view(s: Settings) -> tuple:
    return _rounds(net_key(s))


def edge_values(net, x) -> dict:
    """Zeichnung: Leitungen mit x = 1 (Baum), gebrochene mit Beschriftung, übrige grau."""
    full = [e for e in range(net.m) if x[e] > 1 - 1e-6]
    frac = [e for e in range(net.m) if 1e-6 < x[e] < 1 - 1e-6]
    return {"full": full, "frac": frac, "text": {e: num(x[e]) for e in frac}}


def verdict_lp(s: Settings, v: dict) -> tuple[str, str]:
    if v["value"] > v["opt"] + 1e-6:
        return "error", "Der LP-Wert liegt über dem kleinsten Spannbaum. Das darf nicht sein (das LP ist eine Relaxation): Rechenfehler."
    form = C.FORM_NAMES[s.form].split(":")[0]
    if v["gap"] > 1e-6:
        nfrac = int(np.sum((v["x"] > 1e-6) & (v["x"] < 1 - 1e-6)))
        return "warning", (
            f"**{form}:** Der LP-Wert ist **{num(v['value'])}**, der kleinste Spannbaum kostet **{num(v['opt'])}**: eine **Lücke** von {num(v['gap'])}. "
            f"Die Lösung ist **gebrochen** ({nfrac} Leitungen mit Werten zwischen 0 und 1), sie ist kein Spannbaum."
        )
    if v["fractional"]:
        return "info", f"**{form}:** Der LP-Wert **{num(v['value'])}** ist gleich dem kleinsten Spannbaum, die gefundene Lösung ist aber gebrochen (mehrere optimale Ecken)."
    return "success", f"**{form}:** Der LP-Wert **{num(v['value'])}** ist gleich dem kleinsten Spannbaum, und die Lösung ist **ganzzahlig**: ein Spannbaum."


def round_text(net, rounds: tuple, index: int) -> tuple[str, str]:
    r = rounds[index]
    if r["violation"] is None:
        return "success", f"Runde {index + 1}: **Keine Rangungleichung** ist mehr verletzt. Das LP liegt bei **{num(r['value'])}**" + (
            f", nach {index} ergänzten Ungleichungen." if index else "; die Schnittbedingungen allein reichen hier schon.")
    viol, u = r["violation"]
    inside = inside_edges(net.edges, u)
    lhs = sum(r["x"][e] for e in inside)
    return "info", (
        f"Runde {index + 1}: Das LP liegt bei **{num(r['value'])}**. Die Knotenmenge **{node_names(u, net.n)}** verletzt die Rangungleichung: x(E[U]) = **{num(lhs)}** > |U| − 1 = **{popcount(u) - 1}** "
        f"({len(inside)} Leitungen in U, Verletzung {num(viol)}). Sie wird ergänzt."
    )


def verdict_rounds(net, v: dict, rounds: tuple) -> tuple[str, str]:
    last = rounds[-1]
    if abs(last["value"] - v["opt"]) > 1e-6:
        return "error", "Der Schnittebenenlauf endet nicht beim kleinsten Spannbaum. Das darf nicht sein: Rechenfehler."
    return "success", (
        f"Start: Schnitt-LP **{num(rounds[0]['value'])}**; nach **{len(rounds) - 1}** ergänzten Rangungleichungen: **{num(last['value'])}** = kleinster Spannbaum ({num(v['opt'])})."
        if len(rounds) > 1 else f"Das Schnitt-LP liegt schon bei **{num(last['value'])}**, dem kleinsten Spannbaum: Es ist keine Rangungleichung zu ergänzen."
    )


# --- Experiment 1: Greedy und das Dual ---------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _dual(key: tuple) -> dict:
    net = get_net(*key)
    ok = forest_table(*key)
    r = forest_rank(*key)
    top = max(net.costs) + 1
    w = [top - c for c in net.costs]                        # positive Gewichte: der schwerste Wald ist der billigste Spannbaum
    chosen, value, order = greedy(ok, net.m, w)
    dual = greedy_dual(r, net.m, w)
    chk = dual_check(r, net.m, w, dual)
    lp_value, _x = lp_max(r, net.m, w)
    return {"w": w, "chosen": chosen, "value": value, "order": order, "dual": dual, "check": chk, "lp": lp_value, "kruskal": kruskal(net.n, net.edges, net.costs)[1]}


def dual_view(s: Settings) -> dict:
    return _dual(net_key(s))


def flat_nodes(net, flat: int) -> str:
    """Knotenmengen der Zusammenhangskomponenten des Flats (nur Komponenten mit Leitung)."""
    comp = components(net.n, [net.edges[e] for e in range(net.m) if flat >> e & 1])
    groups = {}
    for v, c in enumerate(comp):
        groups.setdefault(c, []).append(v)
    parts = [node_names(sum(1 << v for v in vs), net.n) for vs in groups.values() if len(vs) > 1]
    return " ".join(parts)


def dual_rows(s: Settings, v: dict) -> list[dict]:
    net, r = net_of(s), forest_rank(*net_key(s))
    return [{"Flat (Knotenmengen)": flat_nodes(net, f), "Leitungen": popcount(f), "Rang": int(r[f]), "y": y} for f, y in v["dual"]]


def verdict_dual(net, v: dict) -> tuple[str, str]:
    chk = v["check"]
    if not chk["feasible"] or abs(chk["value"] - v["value"]) > 1e-9 or abs(v["lp"] - v["value"]) > 1e-6 or v["chosen"] != v["kruskal"]:
        return "error", "Greedy, Dual und LP stimmen nicht überein. Das darf nicht sein: Rechenfehler."
    ganz = "ganzzahlig" if chk["integral"] else "nicht ganzzahlig"
    return "success", (
        f"Greedy wählt **{popcount(v['chosen'])}** Leitungen mit dem Gewicht **{v['value']}**; das ist derselbe Baum wie bei Kruskal. Das Dual hat **{len(v['dual'])}** Flats mit y > 0 (eine Kette), ist zulässig und "
        f"**{ganz}**; sein Wert **{chk['value']}** ist gleich dem Greedy-Wert und gleich dem LP-Wert ({num(v['lp'])})."
    )


# --- Experiment 2: das Polytop kleiner Matroide ------------------------------------------------------------------------------------------------


@lru_cache(maxsize=16)
def poly_view(key: str) -> dict:
    mat = named_matroid(key)
    n, ok = mat["n"], mat["ok"]
    r = rank_table(ok, n)
    verts = polytope_vertices(ok, r, n, mat["base"])
    edges = polytope_edges(ok, r, n, mat["base"])
    out = {"mat": mat, "r": r, "vertices": verts, "edges": edges, "exchange": exchange_pairs(ok, r, n) if mat["base"] else None}
    out["facets"] = facets(ok, r, n, mat["base"])
    return out


def poly_name(mat: dict, mask: int) -> str:
    return "".join(mat["labels"][e] for e in range(mat["n"]) if mask >> e & 1) or "∅"


def poly_greedy(key: str, w) -> dict:
    v = poly_view(key)
    mat = v["mat"]
    chosen, value, order = greedy(mat["ok"], mat["n"], list(w), base=mat["base"])
    lp, x = lp_max(v["r"], mat["n"], list(w), base=mat["base"])
    return {"chosen": chosen, "value": value, "order": order, "lp": lp, "x": _plain(x)}


def verdict_poly(key: str, g: dict) -> tuple[str, str]:
    v = poly_view(key)
    mat = v["mat"]
    art = "Basen" if mat["base"] else "unabhängigen Mengen"
    if abs(g["lp"] - g["value"]) > 1e-6:
        return "error", "Greedy und LP stimmen nicht überein. Das darf nicht sein: Rechenfehler."
    if not mat["base"]:
        kanten = f"es hat **{len(v['edges'])}** Kanten."
    elif set(v["edges"]) == set(v["exchange"]):
        kanten = f"die **{len(v['edges'])}** Kanten sind genau die **{len(v['exchange'])}** Paare von Basen, die sich durch einen Austausch unterscheiden."
    else:
        return "error", "Die Kanten sind nicht gleich den Basenaustauschen. Das darf nicht sein: Rechenfehler."
    return "success", (
        f"Das Polytop hat **{len(v['vertices'])}** Ecken, genau die {art}; {kanten} Greedy wählt **{poly_name(mat, g['chosen'])}** mit Gewicht **{g['value']}**, und das LP über das Polytop hat denselben Wert **{num(g['lp'])}**."
    )


@lru_cache(maxsize=1)
def small_rows() -> tuple:
    return tuple(small_matroid_row(n, C.PLAY_SEED) for n in range(1, C.ENUM_MAX_N + 1))


def small_table(rows) -> list[dict]:
    return [{
        "Elemente n": r["n"], "Matroide": zahl(r["matroids"]), "Ecken = unabhängige Mengen": zahl(r["vertices"]), "Kanten = Basenaustausch": zahl(r["edges"]), "Greedy = LP": zahl(r["greedy"]),
        "Dual zulässig, ganzzahlig, gleicher Wert": zahl(r["dual"]), "Facetten wie die Regel": zahl(r["facets"]), "Trennung = LP-Zulässigkeit": zahl(r["separation"]),
    } for r in rows]


def verdict_small(rows) -> tuple[str, str]:
    bad = sum(r["matroids"] - r[k] for r in rows for k in ("vertices", "edges", "greedy", "dual", "facets", "separation"))
    total = sum(r["matroids"] for r in rows)
    if bad:
        return "error", f"Bei {bad} Prüfungen gilt eine Aussage nicht. Das darf nicht sein: Rechenfehler."
    return "success", (
        f"Bei allen **{zahl(total)}** Matroiden mit höchstens {rows[-1]['n']} Elementen (beschriftet): Die Ecken des Polytops sind die unabhängigen Mengen, die Kanten des Basenpolytops die Basenaustausche, "
        f"Greedy löst das LP, das Greedy-Dual ist zulässig und ganzzahlig, die Facetten sind genau x_e ≥ 0 und die zusammenhängenden Flats, und die Trennung stimmt mit der LP-Zulässigkeit überein (**0 Abweichungen**). Greedy, Dual und Trennung sind je Matroid an zwei ganzen Gewichtsvektoren beziehungsweise drei Testpunkten geprüft."
    )


# --- Experiment 3: Nicht-Matroide ---------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def system_rows() -> tuple:
    return tuple(system_row(n, C.PLAY_SEED, C.SYSTEM_SAMPLE) for n in range(3, C.ENUM_MAX_N + 1))


def system_table(rows) -> list[dict]:
    return [{
        "Elemente n": r["n"], "Systeme": zahl(r["systems"]), "Matroide (alle ganzzahlig)": f"{zahl(r['matroids'])} ({zahl(r['matroids_integral'])})",
        "Nicht-Matroide": zahl(r["non"]), "davon mit ganzzahligem Polytop": zahl(r["non_integral"]),
        "Stichprobe": zahl(r["sample"]), "Greedy scheitert": zahl(r["greedy_fail"]), "LP über dem Optimum": zahl(r["lp_gap"]),
    } for r in rows]


def verdict_system(rows) -> tuple[str, str]:
    if any(r["matroids_integral"] != r["matroids"] for r in rows):
        return "error", "Ein Matroid hat ein Polytop mit gebrochener Ecke. Das darf nicht sein: Rechenfehler."
    last = rows[-1]
    non = sum(r["non"] for r in rows)
    ganz = sum(r["non_integral"] for r in rows)
    return "info", (
        f"Bei **{zahl(non)}** Nicht-Matroiden (n = {rows[0]['n']} bis {last['n']}) ist das Polytop der Rangungleichungen bei **{zahl(ganz)}** trotzdem ganzzahlig: Ganzzahligkeit allein kennzeichnet Matroide **nicht**. "
        f"Was bricht, ist Greedy: In der Stichprobe von {last['sample']} Systemen mit {last['n']} Elementen scheitert Greedy bei mindestens einem von sechs Gewichtsvektoren bei **{zahl(last['greedy_fail'])}**, das LP liegt über dem besten unabhängigen Wert bei **{zahl(last['lp_gap'])}** "
        f"(gebrochene Ecke)."
    )


# --- Experiment 4: Welche Rangungleichungen zählen ------------------------------------------------------------------------------------------------


@lru_cache(maxsize=16)
def _facets(key: tuple) -> dict:
    net = get_net(*key)
    ok = forest_table(*key)
    r = forest_rank(*key)
    flats, conn = flats_of(ok, r, net.m)
    out = {"flats": len(flats), "conn": conn, "ineq": net.m + (1 << net.m) - 1, "checked": net.n <= C.FACET_CHECK_MAX_N, "forests": int(np.sum(ok))}
    if out["checked"]:
        fc = facets(ok, r, net.m)
        out["facets_nn"], out["facets_rk"] = len(fc["nn"]), len(fc["rank"])
        out["rule"] = set(fc["rank"]) == set(conn) and len(fc["nn"]) == net.m
    return out


def facet_view(s: Settings) -> dict:
    return _facets(net_key(s))


def facet_rows(s: Settings, v: dict) -> list[dict]:
    net, r = net_of(s), forest_rank(*net_key(s))
    return [{"Knotenmengen des Flats": flat_nodes(net, f), "Leitungen": popcount(f), "Rang": int(r[f])} for f in sorted(v["conn"], key=lambda f: (popcount(f), f))]


def verdict_facets(net, v: dict) -> tuple[str, str]:
    kopf = f"Das Waldpolytop dieses Netzes hat **{zahl(v['ineq'])}** Ungleichungen (x_e ≥ 0 für jede Leitung und eine Rangungleichung je nichtleerer Leitungsmenge), und es gibt **{v['flats']}** Flats, davon **{len(v['conn'])}** zusammenhängende. "
    if not v["checked"]:
        return "info", kopf + f"Bei {net.n} Standorten werden die Facetten nicht aus den Ecken nachgerechnet (zu viele Ungleichungen); die Regel (x_e ≥ 0 und die zusammenhängenden Flats) liefert {net.m + len(v['conn'])}."
    total = v["facets_nn"] + v["facets_rk"]
    if not v["rule"]:
        return "error", kopf + "Die Facetten sind nicht gleich der Regel. Das darf nicht sein: Rechenfehler."
    return "success", kopf + (
        f"Nachgerechnet aus den **{zahl(v['forests'])}** Ecken (Wäldern) sind nur **{total}** davon Facetten: **{v['facets_nn']}** der Form x_e ≥ 0 und **{v['facets_rk']}** Rangungleichungen, "
        f"und das sind genau die zusammenhängenden Flats. Alle übrigen **{zahl(v['ineq'] - total)}** Ungleichungen sind überflüssig."
    )


# --- Experiment 5: Trennproblem --------------------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _separation(key: tuple) -> dict:
    net = get_net(*key)
    r = forest_rank(*key)
    x = _rounds(key)[0]["x"]
    by_edges, arg = separate(r, net.m, x)
    best = violated_set(net.n, net.edges, x)
    return {"x": x, "by_edges": by_edges, "edge_set": arg, "node": best}


def sep_view(s: Settings) -> dict:
    return _separation(net_key(s))


def verdict_sep(net, v: dict) -> tuple[str, str]:
    kantenmengen = (1 << net.m) - 1
    knotenmengen = (1 << net.n) - net.n - 1
    by_edges_violated = v["by_edges"] < -1e-9
    if by_edges_violated != (v["node"] is not None):
        return "error", "Die Suche über Kantenmengen und die über Knotenmengen kommen zu verschiedenen Ergebnissen. Das darf nicht sein: Rechenfehler."
    if v["node"] is None:
        return "success", (
            f"Die Lösung des Schnitt-LP liegt im Waldpolytop: Keine der **{zahl(kantenmengen)}** Leitungsmengen und keine der **{zahl(knotenmengen)}** Knotenmengen verletzt eine Rangungleichung."
        )
    viol, u = v["node"]
    inside = inside_edges(net.edges, u)
    return "warning", (
        f"Die Lösung des Schnitt-LP liegt **nicht** im Waldpolytop. Über alle **{zahl(kantenmengen)}** Leitungsmengen ist der kleinste Wert von r(S) − x(S) gleich **{num(v['by_edges'])}** "
        f"(bei {len(_edge_set(v['edge_set'], net.m))} Leitungen); über nur **{zahl(knotenmengen)}** Knotenmengen findet man dieselbe Aussage: U = {node_names(u, net.n)} mit {len(inside)} Leitungen, "
        f"x(E[U]) = {num(sum(v['x'][e] for e in inside))} > {popcount(u) - 1}."
    )


def _edge_set(mask: int, m: int) -> list[int]:
    return [e for e in range(m) if mask >> e & 1]


# --- Experiment 6: zwei und drei Polytope --------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def pair_rows() -> tuple:
    return tuple(pair_row(n, C.PLAY_SEED, C.PAIR_SAMPLE) for n in range(1, C.ENUM_MAX_N + 1))


@lru_cache(maxsize=1)
def triple_rows() -> tuple:
    return tuple(triple_row(n) for n in (2, 3))


@lru_cache(maxsize=1)
def triangle() -> dict:
    return triangle_example()


def pair_table(rows) -> list[dict]:
    return [{"Elemente n": r["n"], "Paare": zahl(r["pairs"]), "alle Ecken ganzzahlig": zahl(r["integral"]), "Ecken = gemeinsame unabhängige Mengen": zahl(r["common"])} for r in rows]


def triple_table(rows) -> list[dict]:
    return [{"Elemente n": r["n"], "Tripel": zahl(r["triples"]), "mit gebrochener Ecke": zahl(r["fractional"])} for r in rows]


def verdict_pairs(rows, trows) -> tuple[str, str]:
    if any(r["integral"] != r["pairs"] or r["common"] != r["pairs"] for r in rows):
        return "error", "Der Schnitt zweier Matroid-Polytope hat eine gebrochene Ecke. Das darf nicht sein: Rechenfehler."
    pairs = sum(r["pairs"] for r in rows)
    t3 = trows[-1]
    tri = triangle()
    return "success", (
        f"Bei allen **{zahl(pairs)}** geprüften Paaren von Matroiden mit höchstens {rows[-1]['n']} Elementen sind alle Ecken des Schnitts ganzzahlig und genau die gemeinsamen unabhängigen Mengen. "
        f"Bei drei Matroiden gilt das nicht: Von **{zahl(t3['triples'])}** Tripeln mit {t3['n']} Elementen haben **{zahl(t3['fractional'])}** eine gebrochene Ecke, zum Beispiel ({', '.join(num(v) for v in tri['fractional'][0])}) beim Dreieck."
    )


# --- Messreihe über Pläne -----------------------------------------------------------------------------------------------------------------------


def _plan_make(n: int, seed: int):
    net = get_net("plan", n, seed)
    return net.edges, net.costs


@lru_cache(maxsize=1)
def plan_series() -> tuple:
    return tuple(plan_series_row(n, C.SERIES_SEEDS, _plan_make) for n in C.SERIES_N)


def series_table(rows) -> list[dict]:
    return [{"Standorte": r["n"], "Pläne": r["plans"], "Schnitt-LP mit Lücke": r["cut_gap"], "Partitions-LP mit Lücke": r["partition_gap"], "Rang-LP mit Lücke": r["rank_gap"], "längster Schnittebenenlauf (Runden)": r["rounds_max"]} for r in rows]


def verdict_series(rows) -> tuple[str, str]:
    if any(r["partition_gap"] or r["rank_gap"] for r in rows):
        return "error", "Das Partitions-LP oder das Rang-LP hat eine Lücke. Das darf nicht sein: Rechenfehler."
    shares = ", ".join(f"{prozent(r['cut_gap'] / r['plans'], 0)} %" for r in rows)
    return "info", (
        f"Bei Plänen mit 6, 7, 8 Standorten hat das Schnitt-LP bei {shares} der {rows[0]['plans']} Pläne eine Lücke; das Partitions-LP und das Rang-LP bei **keinem**. "
        f"Der Schnittebenenlauf braucht bei diesen Plänen höchstens {max(r['rounds_max'] for r in rows)} Runden."
    )


# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------------


def play_view(s: Settings, full: tuple, half: tuple) -> dict:
    """Ein Punkt x auf den Leitungen: 1 auf `full`, ½ auf `half` (sonst 0). Liegt er im Waldpolytop? Sonst die stärkste verletzte Knotenmenge."""
    net = net_of(s)
    x = np.zeros(net.m)
    for e in half:
        x[e] = 0.5
    for e in full:
        x[e] = 1.0
    return {"x": x, "node": violated_set(net.n, net.edges, x), "sum": float(x.sum())}


def verdict_play(s: Settings, v: dict) -> tuple[str, str]:
    net = net_of(s)
    if v["sum"] == 0:
        return "info", "Wählen Sie Leitungen mit x = 1 oder x = ½."
    if v["node"] is None:
        return "success", f"Der Punkt mit x(E) = {num(v['sum'])} liegt im **Waldpolytop**: Er ist eine Konvexkombination von Wäldern (keine Rangungleichung ist verletzt)."
    viol, u = v["node"]
    inside = inside_edges(net.edges, u)
    return "warning", (
        f"Der Punkt liegt **nicht** im Waldpolytop: Die Knotenmenge {node_names(u, net.n)} hat x(E[U]) = **{num(sum(v['x'][e] for e in inside))}** > |U| − 1 = **{popcount(u) - 1}** "
        f"({len(inside)} Leitungen in U)."
    )
