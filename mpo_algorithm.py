"""Kern: Tabellen von Matroiden (Wald, Partition), Rang, Unabhängigkeitssysteme, Greedy, Dual, Polytope (Ecken, Facetten, Kanten), Spannbaum-LP mit Schnittebenen.

Matroide und Systeme sind Tabellen über alle Teilmengen (Maske → unabhängig?), wie in den Stücken davor; Mengen sind Bitmasken."""

import itertools
import random
from dataclasses import dataclass, field
from functools import cached_property

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import HalfspaceIntersection


def popcount(x: int) -> int:
    return bin(x).count("1")


def elements(mask: int, m: int) -> list[int]:
    return [e for e in range(m) if mask >> e & 1]


class System:
    """Unabhängigkeitssystem auf m Elementen; ok[mask] sagt, ob die Menge `mask` zulässig ist."""

    def __init__(self, name: str, m: int, ok):
        if not 1 <= m <= 16:
            raise ValueError(f"m = {m} außerhalb von 1 bis 16")
        if len(ok) != 1 << m or not ok[0]:
            raise ValueError("ok braucht 2**m Einträge, und die leere Menge muss zulässig sein")
        self.name, self.m, self.ok = name, m, list(ok)
        self.full = (1 << m) - 1
        self.ind = [mask for mask in range(1 << m) if self.ok[mask]]
        self.ind_array = np.array(self.ind, dtype=np.int64)
        self.sizes = np.array([popcount(i) for i in self.ind], dtype=np.int64)
        self._ranks()

    # --- Grundbegriffe ------------------------------------------------------------------------------------------------------------------

    def check_down_closed(self) -> bool:
        """Mit jeder zulässigen Menge sind alle Mengen ohne ein Element zulässig (genügt für alle Teilmengen)."""
        return all(self.ok[mask & ~(1 << e)] for mask in self.ind for e in range(self.m) if mask >> e & 1)

    def can_add(self, mask: int, e: int) -> bool:
        return not mask >> e & 1 and self.ok[mask | 1 << e]

    def addable(self, mask: int) -> int:
        """Maske aller Elemente, die zu `mask` passen."""
        out = 0
        for e in range(self.m):
            if self.can_add(mask, e):
                out |= 1 << e
        return out

    def is_maximal(self, mask: int) -> bool:
        return self.ok[mask] and self.addable(mask) == 0

    def _ranks(self):
        m, ok = self.m, self.ok
        ur = [0] * (1 << m)
        for mask in range(1, 1 << m):
            ur[mask] = popcount(mask) if ok[mask] else max(ur[mask & ~(1 << e)] for e in range(m) if mask >> e & 1)
        self.ur = ur
        lr = [0] * (1 << m)
        for i in sorted(self.ind, key=popcount):
            free = self.full & ~i & ~self.addable(i)
            s = free
            while True:
                f = i | s
                if f and lr[f] == 0:
                    lr[f] = popcount(i)
                if s == 0:
                    break
                s = (s - 1) & free
        self.lr = lr
        best = None
        for f in range(1, 1 << m):
            if ur[f] > 0:
                q = lr[f] / ur[f]
                if best is None or q < best[0] - 1e-15:
                    best = (q, f)
        self.q = best[0] if best else 1.0

    # --- Rang, Basen, Kreise, Abschluss, Flache -------------------------------------------------------------------------------------------

    @property
    def rank(self) -> int:
        """Rang der ganzen Grundmenge: Größe der größten zulässigen Menge."""
        return self.ur[self.full]

    def rank_of(self, f: int) -> int:
        return self.ur[f]

    @cached_property
    def bases(self) -> list[int]:
        """Maximale zulässige Mengen (bei einem Matroid alle gleich groß)."""
        return [i for i in self.ind if self.is_maximal(i)]

    @cached_property
    def circuits(self) -> list[int]:
        """Minimale unzulässige Mengen."""
        out = []
        for c in range(1, 1 << self.m):
            if not self.ok[c] and all(self.ok[c & ~(1 << e)] for e in range(self.m) if c >> e & 1):
                out.append(c)
        return out

    def closure(self, f: int) -> int:
        """cl(F) = F plus alle e, deren Hinzunahme den Rang nicht erhöht."""
        r = self.ur[f]
        out = f
        for e in range(self.m):
            if not f >> e & 1 and self.ur[f | 1 << e] == r:
                out |= 1 << e
        return out

    @cached_property
    def closures(self) -> list[int]:
        return [self.closure(f) for f in range(1 << self.m)]

    @cached_property
    def flats(self) -> list[int]:
        return [f for f in range(1 << self.m) if self.closures[f] == f]

    def flats_by_rank(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for f in self.flats:
            out[self.ur[f]] = out.get(self.ur[f], 0) + 1
        return dict(sorted(out.items()))

    def circuits_in(self, mask: int) -> list[int]:
        """Alle Kreise, die in `mask` enthalten sind."""
        return [c for c in self.circuits if c & ~mask == 0]

    def fundamental_circuit(self, base: int, e: int):
        """Der Kreis in B + e, wenn es genau einen gibt (bei einem Matroid immer), sonst None."""
        inside = self.circuits_in(base | 1 << e)
        return inside[0] if len(inside) == 1 else None

    def swap_is_basis(self, base: int, f: int, e: int) -> bool:
        """Ist B − f + e wieder eine Basis (maximale zulässige Menge)?"""
        new = (base & ~(1 << f)) | 1 << e
        return self.is_maximal(new)

    def maximal_sizes(self) -> dict[int, int]:
        sizes: dict[int, int] = {}
        for i in self.bases:
            sizes[popcount(i)] = sizes.get(popcount(i), 0) + 1
        return dict(sorted(sizes.items()))

    # --- Austauschprobe (Stück 3) -------------------------------------------------------------------------------------------------------

    def exchange_scan(self, weak: bool = False) -> tuple[int, int]:
        """(Zahl der Paare (I1, I2) mit |I1| < |I2|, Zahl der Paare ohne Austauschpartner); je I1 ein Maskenvergleich über alle I2."""
        pairs = viol = 0
        for i1, s1 in zip(self.ind, self.sizes):
            bigger = self.sizes == s1 + 1 if weak else self.sizes > s1
            count = int(bigger.sum())
            if not count:
                continue
            pairs += count
            viol += int(((self.ind_array[bigger] & ~i1 & self.addable(i1)) == 0).sum())
        return pairs, viol

    @cached_property
    def is_matroid(self) -> bool:
        return self.exchange_scan()[1] == 0


_PC = None


def pc_table() -> np.ndarray:
    """Elementzahl aller Masken bis 2^16."""
    global _PC
    if _PC is None:
        _PC = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.int16)
    return _PC


def rank_table(ok: np.ndarray, m: int) -> np.ndarray:
    """Rang jeder Teilmenge: Größe der größten unabhängigen Teilmenge (Schichten nach Elementzahl, mit numpy)."""
    pc = pc_table()[: 1 << m]
    ur = np.zeros(1 << m, dtype=np.int16)
    idx = np.arange(1 << m)
    for k in range(1, m + 1):
        layer = idx[pc == k]
        best = np.zeros(len(layer), dtype=np.int16)
        for e in range(m):
            has = (layer >> e & 1) == 1
            sub = ur[layer[has] & ~(1 << e)]
            best[has] = np.maximum(best[has], sub)
        ur[layer] = np.where(ok[layer], k, best)
    return ur


def partition_table(m: int, classes, caps=None) -> np.ndarray:
    """Partitionsmatroid: je Klasse höchstens caps[klasse] Elemente (Standard 1)."""
    caps = caps or {}
    pc = pc_table()[: 1 << m]
    idx = np.arange(1 << m)
    ok = np.ones(1 << m, dtype=bool)
    for cls in set(classes):
        mask = sum(1 << e for e in range(m) if classes[e] == cls)
        ok &= pc[idx & mask] <= caps.get(cls, 1)
    return ok


def graphic_table(v: int, edges) -> np.ndarray:
    """Graphisches Matroid der Kantenliste auf v Knoten (Schleifen sind nie unabhängig)."""
    m = len(edges)
    ok = np.zeros(1 << m, dtype=bool)
    for mask in range(1 << m):
        parent = list(range(v))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        good = True
        for e in range(m):
            if mask >> e & 1:
                a, b = find(edges[e][0]), find(edges[e][1])
                if a == b:
                    good = False
                    break
                parent[a] = b
        ok[mask] = good
    return ok


def all_systems(n: int) -> list[tuple[bool, ...]]:
    """Alle nach unten abgeschlossenen Familien auf n Elementen mit leerer Menge, jeweils als Tupel ok[mask]."""
    masks = sorted(range(1 << n), key=lambda x: (popcount(x), x))
    out: list[tuple[bool, ...]] = []
    family = [False] * (1 << n)

    def rec(i):
        if i == len(masks):
            if family[0]:
                out.append(tuple(family))
            return
        mask = masks[i]
        allowed = mask == 0 or all(family[mask & ~(1 << e)] for e in range(n) if mask >> e & 1)
        family[mask] = False
        rec(i + 1)
        if allowed:
            family[mask] = True
            rec(i + 1)
            family[mask] = False

    rec(0)
    return out


def small_matroids(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Alle Matroide auf n Elementen als (Tabelle der unabhängigen Mengen, Rangtabelle)."""
    out = []
    for ok in all_systems(n):
        s = System("x", n, list(ok))
        if s.exchange_scan()[1] == 0:
            out.append((np.array(s.ok, dtype=bool), np.array(s.ur, dtype=np.int16)))
    return out


def components(n: int, edge_list) -> list[int]:
    """Klassenindex (ab 0) je Knoten: Zusammenhangskomponenten des Graphen mit den Kanten edge_list."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edge_list:
        parent[find(a)] = find(b)
    roots = sorted({find(v) for v in range(n)})
    return [roots.index(find(v)) for v in range(n)]


def set_partitions(n: int):
    """Alle Partitionen von {0, …, n − 1} als Klassenindex je Knoten (restricted growth strings)."""
    def rec(i, cur, mx):
        if i == n:
            yield tuple(cur)
            return
        for c in range(mx + 2):
            cur.append(c)
            yield from rec(i + 1, cur, max(mx, c))
            cur.pop()
    yield from rec(0, [], -1)


# --- Polytope: Ecken, Rangungleichungen, Greedy, Dual ---------------------------------------------------------------------------------------------


def indicator(mask: int, n: int) -> np.ndarray:
    return np.array([(mask >> e) & 1 for e in range(n)], dtype=float)


def nonloops(ok, n: int) -> list[int]:
    return [e for e in range(n) if ok[1 << e]]


def _clean(v: float) -> float:
    return round(float(v), 6) + 0.0


def vertices(oks, n: int) -> set:
    """Ecken von {x ≥ 0 : x(S) ≤ r_i(S) für jedes Matroid (jedes System) i und jede Menge S} (Qhull); Schlingen sind 0. Mit einer Tabelle: das Unabhängigkeitspolytop,
    mit zwei oder drei: der Schnitt der Polytope. Rückgabe: Menge von Tupeln der Länge n."""
    ranks = [rank_table(np.asarray(ok, dtype=bool), n) for ok in oks]
    nl = [e for e in range(n) if all(ok[1 << e] for ok in oks)]
    d = len(nl)
    if d == 0:
        return {tuple([0.0] * n)}
    if d == 1:
        return {tuple([0.0] * n), tuple(1.0 if e == nl[0] else 0.0 for e in range(n))}
    rows, rhs = [], []
    for j in range(d):
        row = np.zeros(d)
        row[j] = -1.0
        rows.append(row)
        rhs.append(0.0)
    for r in ranks:
        for sub in range(1, 1 << d):
            mask = sum(1 << nl[j] for j in range(d) if sub >> j & 1)
            rows.append(np.array([(sub >> j) & 1 for j in range(d)], dtype=float))
            rhs.append(float(r[mask]))
    hs = np.hstack([np.array(rows), -np.array(rhs)[:, None]])
    pts = HalfspaceIntersection(hs, np.full(d, 0.5 / d)).intersections
    out = set()
    for p in pts:
        full = [0.0] * n
        for j in range(d):
            full[nl[j]] = _clean(p[j])
        out.add(tuple(full))
    return out


def indep_indicators(ok, n: int) -> set:
    return {tuple(float(x) for x in indicator(m, n)) for m in range(1 << n) if ok[m]}


def is_integral(verts) -> bool:
    return all(abs(v - round(v)) < 1e-6 for p in verts for v in p)


def rank_rows(n: int):
    """Matrix der Mengen-Indikatoren aller nichtleeren Teilmengen (Zeile m − 1 gehört zur Menge m)."""
    return np.array([[(m >> e) & 1 for e in range(n)] for m in range(1, 1 << n)], dtype=float)


def lp_max(r, n: int, w, base: bool = False):
    """max w·x über {x ≥ 0, x(S) ≤ r(S)} (mit x(E) = r(E), wenn base). Rückgabe: (Wert, x)."""
    kw = {}
    if base:
        kw = dict(A_eq=np.ones((1, n)), b_eq=[float(r[(1 << n) - 1])])
    res = linprog(-np.asarray(w, dtype=float), A_ub=rank_rows(n), b_ub=np.array([r[m] for m in range(1, 1 << n)], dtype=float), bounds=[(0, None)] * n, method="highs", **kw)
    return -float(res.fun), res.x


def greedy(ok, n: int, w, base: bool = False):
    """Greedy nach absteigendem Gewicht (Gleichstand: kleinere Nummer zuerst). Beim Unabhängigkeitspolytop nur Elemente mit positivem Gewicht, bei der Basis alle.
    Rückgabe: (Menge, Wert, Reihenfolge)."""
    order = sorted(range(n), key=lambda e: (-w[e], e))
    cur, val = 0, 0
    for e in order:
        if (base or w[e] > 0) and ok[cur | 1 << e]:
            cur |= 1 << e
            val += w[e]
    return cur, val, order


def closure_mask(r, n: int, s: int) -> int:
    out = s
    for e in range(n):
        if r[s | 1 << e] == r[s]:
            out |= 1 << e
    return out


def greedy_dual(r, n: int, w) -> list[tuple[int, int]]:
    """Dual zu max w·x über das Unabhängigkeitspolytop (Gewichte ≥ 0): y auf den Hüllen der Präfixmengen der Gewichtsreihenfolge, y = Gewichtsdifferenz zum nächsten Element.
    Rückgabe: [(Flat, y)] nach Größe des Flats."""
    order = sorted(range(n), key=lambda e: (-w[e], e))
    out: dict[int, int] = {}
    pref = 0
    for i, e in enumerate(order):
        pref |= 1 << e
        nxt = w[order[i + 1]] if i + 1 < n else 0
        d = w[e] - nxt
        if d > 0:
            c = closure_mask(r, n, pref)
            out[c] = out.get(c, 0) + d
    return sorted(out.items(), key=lambda t: (popcount(t[0]), t[0]))


def dual_check(r, n: int, w, dual) -> dict:
    cover = [sum(y for s, y in dual if s >> e & 1) for e in range(n)]
    return {"feasible": all(cover[e] >= w[e] for e in range(n)), "value": sum(y * int(r[s]) for s, y in dual), "integral": all(float(y).is_integer() for _, y in dual)}


def flats_of(ok, r, n: int):
    """Flats ohne Schlingen und ihre zusammenhängenden unter ihnen (Rangsummenregel: keine Aufteilung in zwei Teile mit r(A) + r(B) = r(F))."""
    nl = nonloops(ok, n)
    nlmask = sum(1 << e for e in nl)
    flats = [s for s in range(1, 1 << n) if not s & ~nlmask and all(r[s | 1 << e] > r[s] for e in nl if not s >> e & 1)]
    conn = []
    for f in flats:
        good = True
        sub = (f - 1) & f
        while sub:
            if r[sub] + r[f & ~sub] == r[f]:
                good = False
                break
            sub = (sub - 1) & f
        if good:
            conn.append(f)
    return flats, conn


def polytope_vertices(ok, r, n: int, base: bool) -> list[int]:
    full = int(r[(1 << n) - 1])
    return [m for m in range(1 << n) if ok[m] and (not base or popcount(m) == full)]


def _constraints(ok, r, n: int):
    nl = nonloops(ok, n)
    nlmask = sum(1 << e for e in nl)
    cons = [("nn", 1 << e) for e in nl] + [("rk", s) for s in range(1, 1 << n) if not s & ~nlmask]

    def tight(v: int, c) -> bool:
        kind, s = c
        return (v & s) == 0 if kind == "nn" else popcount(v & s) == int(r[s])

    return nl, cons, tight


def facets(ok, r, n: int, base: bool = False) -> dict:
    """Facetten von P(M) (oder B(M)): Ungleichung ist Facette, wenn die auf ihr liegenden Ecken die affine Dimension d − 1 haben (Rang von [Ecken, 1] gleich d, hier d = Dimension des Polytops + 1).
    Rückgabe: {"nn": [Elemente], "rank": [Mengen], "total": Zahl der Ungleichungen, "dim": Dimension}."""
    nl, cons, tight = _constraints(ok, r, n)
    d = len(nl)
    verts = polytope_vertices(ok, r, n, base)
    if d == 0 or not verts:
        return {"nn": [], "rank": [], "total": 0, "dim": 0}
    pts = np.array([indicator(v, n)[nl] for v in verts])
    dim = int(np.linalg.matrix_rank(np.hstack([pts, np.ones((len(pts), 1))]))) - 1
    nn, rk = [], []
    for c in cons:
        sel = [v for v in verts if tight(v, c)]
        if not sel:
            continue
        tv = np.array([indicator(v, n)[nl] for v in sel])
        if int(np.linalg.matrix_rank(np.hstack([tv, np.ones((len(tv), 1))]))) - 1 == dim - 1:
            (nn if c[0] == "nn" else rk).append(c[1])
    return {"nn": [int(m).bit_length() - 1 for m in nn], "rank": rk, "total": len(cons), "dim": dim}


def polytope_edges(ok, r, n: int, base: bool = False) -> list[tuple[int, int]]:
    """Kanten des Polytops: zwei Ecken sind benachbart, wenn die Ecken, die auf allen gemeinsam scharfen Ungleichungen liegen, genau diese beiden sind."""
    verts = polytope_vertices(ok, r, n, base)
    nl, cons, tight = _constraints(ok, r, n)
    scharf = {v: frozenset(c for c in cons if tight(v, c)) for v in verts}
    out = []
    for a, b in itertools.combinations(verts, 2):
        common = scharf[a] & scharf[b]
        if sum(1 for v in verts if common <= scharf[v]) == 2:
            out.append((a, b))
    return out


def exchange_pairs(ok, r, n: int) -> list[tuple[int, int]]:
    bases = polytope_vertices(ok, r, n, True)
    return [(a, b) for a, b in itertools.combinations(bases, 2) if popcount(a ^ b) == 2]


def separate(r, n: int, x) -> tuple[float, int]:
    """Trennproblem: kleinster Wert von r(S) − x(S) über alle nichtleeren Mengen S und eine Menge, die ihn annimmt (kleinste Maske)."""
    best, arg = None, 0
    for s in range(1, 1 << n):
        val = float(r[s]) - sum(x[e] for e in range(n) if s >> e & 1)
        if best is None or val < best - 1e-12:
            best, arg = val, s
    return best, arg


def in_hull(ok, n: int, x) -> bool:
    """Liegt x unter einer Konvexkombination unabhängiger Mengen? (LP-Zulässigkeit)"""
    ind = [m for m in range(1 << n) if ok[m]]
    mat = np.array([indicator(m, n) for m in ind]).T
    res = linprog(np.zeros(len(ind)), A_ub=-mat, b_ub=-np.asarray(x, dtype=float), A_eq=np.ones((1, len(ind))), b_eq=[1.0], bounds=[(0, None)] * len(ind), method="highs")
    return res.status == 0


# --- Spannbaum-LP auf einem Netz --------------------------------------------------------------------------------------------------------------


def kruskal(n: int, edges, cost) -> tuple[float, int]:
    """Kleinster Spannbaum: (Kosten, Kantenmenge als Maske); Gleichstand: kleinere Nummer zuerst."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total, chosen = 0, 0
    for e in sorted(range(len(edges)), key=lambda e: (cost[e], e)):
        a, b = find(edges[e][0]), find(edges[e][1])
        if a != b:
            parent[a] = b
            total += cost[e]
            chosen |= 1 << e
    return total, chosen


def inside_edges(edges, u: int) -> list[int]:
    return [e for e, (a, b) in enumerate(edges) if u >> a & 1 and u >> b & 1]


def tree_rows(n: int, edges, kind: str):
    """Ungleichungen des Spannbaum-LP in der Form A x ≤ b: „cut“ (jeder Schnitt wird überquert), „partition“ (jede Partition mit k Klassen hat k − 1 Kanten dazwischen),
    „rank“ (Rangungleichungen des Waldmatroids: höchstens |U| − 1 Kanten in jeder Knotenmenge U)."""
    rows, rhs = [], []
    if kind == "cut":
        for sub in range(1 << (n - 1)):
            s = 1 | (sub << 1)
            if s != (1 << n) - 1:
                rows.append([-(1 if ((s >> a & 1) != (s >> b & 1)) else 0) for a, b in edges])
                rhs.append(-1)
    elif kind == "partition":
        for part in set_partitions(n):
            k = max(part) + 1
            if k >= 2:
                rows.append([-(1 if part[a] != part[b] else 0) for a, b in edges])
                rhs.append(-(k - 1))
    elif kind == "rank":
        for u in range(1, 1 << n):
            if popcount(u) >= 2:
                rows.append([1 if (u >> a & 1 and u >> b & 1) else 0 for a, b in edges])
                rhs.append(popcount(u) - 1)
    else:
        raise ValueError(f"unbekannte Formulierung: {kind}")
    return rows, rhs


def tree_lp(n: int, edges, cost, kind: str, extra=()):
    """min cost·x mit x(E) = n − 1, 0 ≤ x ≤ 1 und den Ungleichungen der Formulierung (plus extra: [(Zeile, rechte Seite)]). Rückgabe: (Wert, x)."""
    rows, rhs = tree_rows(n, edges, kind)
    for row, b in extra:
        rows.append(list(row))
        rhs.append(b)
    res = linprog(np.asarray(cost, dtype=float), A_ub=np.array(rows, dtype=float), b_ub=np.array(rhs, dtype=float), A_eq=np.ones((1, len(edges))), b_eq=[n - 1], bounds=[(0, 1)] * len(edges), method="highs")
    return float(res.fun), np.asarray(res.x)


def violated_set(n: int, edges, x):
    """Stärkste verletzte Rangungleichung x(E[U]) ≤ |U| − 1 über alle Knotenmengen U mit mindestens zwei Knoten: (Verletzung, U) oder None."""
    best = None
    for u in range(1, 1 << n):
        if popcount(u) < 2:
            continue
        viol = sum(x[e] for e in inside_edges(edges, u)) - (popcount(u) - 1)
        if viol > 1e-7 and (best is None or viol > best[0] + 1e-12):
            best = (viol, u)
    return best


def is_fractional(x) -> bool:
    return bool(np.any((x > 1e-6) & (x < 1 - 1e-6)))


def cutting_plane(n: int, edges, cost, max_rounds: int = 20) -> list[dict]:
    """Schnittebenenlauf: Start mit dem Schnitt-LP; verletzte Rangungleichung (stärkste) ergänzen und neu lösen, bis keine mehr verletzt ist.
    Rückgabe: Runden [{"x", "value", "violation": (Verletzung, U) oder None}]; die letzte hat violation None."""
    extra, rounds = [], []
    for _ in range(max_rounds + 1):
        value, x = tree_lp(n, edges, cost, "cut", extra)
        v = violated_set(n, edges, x)
        rounds.append({"x": x, "value": value, "violation": v})
        if v is None:
            break
        u = v[1]
        extra.append(([1 if e in inside_edges(edges, u) else 0 for e in range(len(edges))], popcount(u) - 1))
    return rounds


# --- kleine Matroide für die 3D-Ansicht ---------------------------------------------------------------------------------------------------------


def uniform_table(n: int, r: int) -> np.ndarray:
    return np.array([popcount(m) <= r for m in range(1 << n)])


def named_matroid(key: str) -> dict:
    """Die fünf Matroide der 3D-Ansicht: {"ok", "n", "base": Basenpolytop?, "labels"}."""
    if key == "u23":
        return {"ok": uniform_table(3, 2), "n": 3, "base": False, "labels": "abc"}
    if key == "teil3":
        return {"ok": partition_table(3, [0, 0, 1], {0: 1, 1: 1}), "n": 3, "base": False, "labels": "abc"}
    if key == "u24":
        return {"ok": uniform_table(4, 2), "n": 4, "base": True, "labels": "abcd"}
    if key == "u14":
        return {"ok": uniform_table(4, 1), "n": 4, "base": True, "labels": "abcd"}
    if key == "u24p":
        ok = uniform_table(4, 2).copy()
        for m in range(16):
            if m & 0b11 == 0b11:
                ok[m] = False                                  # a und b parallel: {a, b} abhängig
        return {"ok": ok, "n": 4, "base": True, "labels": "abcd"}
    raise ValueError(f"unbekanntes Matroid: {key}")


# --- Messzeilen für die Tabellen (auf Abruf) -----------------------------------------------------------------------------------------------------


def small_matroid_row(n: int, seed: int, weights: int = 2, points: int = 3) -> dict:
    """Alle Matroide auf n Elementen: Ecken des Unabhängigkeitspolytops = unabhängige Mengen; Kanten des Basenpolytops = Basenaustausche; Greedy = LP (Wert, ganze Gewichte 0 bis 9,
    und beim Basenpolytop Gewichte −5 bis 9); Dual aus Greedy zulässig, ganzzahlig und gleich dem Wert; Facetten: x_e ≥ 0 für jedes Element ohne Schlinge und x(F) ≤ r(F) genau
    für zusammenhängende Flats; Trennung (Minimum über alle Mengen) gleich LP-Zulässigkeit an Gitterpunkten 1/6."""
    rng = random.Random(seed + n)
    mats = small_matroids(n)
    row = {"n": n, "matroids": len(mats), "vertices": 0, "edges": 0, "greedy": 0, "dual": 0, "facets": 0, "separation": 0, "tests": 0, "edge_count": 0}
    for ok, r in mats:
        row["vertices"] += vertices([ok], n) == indep_indicators(ok, n)
        ex, pe = set(exchange_pairs(ok, r, n)), set(polytope_edges(ok, r, n, True))
        row["edges"] += ex == pe
        row["edge_count"] += len(pe)
        good = dual_good = True
        for _ in range(weights):
            w = [rng.randint(0, 9) for _ in range(n)]
            val, _x = lp_max(r, n, w)
            good &= abs(val - greedy(ok, n, w)[1]) < 1e-6
            dual = greedy_dual(r, n, w)
            chk = dual_check(r, n, w, dual)
            dual_good &= chk["feasible"] and chk["integral"] and abs(chk["value"] - val) < 1e-6
            wb = [rng.randint(-5, 9) for _ in range(n)]
            vb, _xb = lp_max(r, n, wb, base=True)
            good &= abs(vb - greedy(ok, n, wb, base=True)[1]) < 1e-6
        row["greedy"] += good
        row["dual"] += dual_good
        fc = facets(ok, r, n)
        flats, conn = flats_of(ok, r, n)
        row["facets"] += set(fc["rank"]) == set(conn) and len(fc["nn"]) == len(nonloops(ok, n))
        sep_good = True
        for _ in range(points):
            x = [rng.randint(0, 6) / 6 for _ in range(n)]
            sep_good &= (separate(r, n, x)[0] < -1e-9) == (not in_hull(ok, n, x))
        row["separation"] += sep_good
        row["tests"] += 1
    return row


def system_row(n: int, seed: int, sample: int = 150, weights: int = 6) -> dict:
    """Alle Unabhängigkeitssysteme auf n Elementen: Polytop der Rangungleichungen ganzzahlig? Bei Nicht-Matroiden: Greedy gegen LP gegen Optimum (ganze Gewichte 1 bis 9),
    an allen bis n = 4 und an einer Stichprobe bei n = 5."""
    rng = random.Random(seed + 100 + n)
    systems = all_systems(n)
    row = {"n": n, "systems": len(systems), "matroids": 0, "matroids_integral": 0, "non": 0, "non_integral": 0, "sample": 0, "greedy_fail": 0, "lp_gap": 0}
    non = []
    for ok in systems:
        mat = System("s", n, [bool(x) for x in ok]).exchange_scan()[1] == 0
        integral = vertices([ok], n) == indep_indicators(ok, n)
        row["matroids"] += mat
        row["matroids_integral"] += mat and integral
        if not mat:
            row["non"] += 1
            row["non_integral"] += integral
            non.append(ok)
    chosen = non if len(non) <= sample else rng.sample(non, sample)
    for ok in chosen:
        r = rank_table(np.asarray(ok, dtype=bool), n)
        fail = gap = False
        for _ in range(weights):
            w = [rng.randint(1, 9) for _ in range(n)]
            best = max(sum(w[e] for e in range(n) if m >> e & 1) for m in range(1 << n) if ok[m])
            val, _x = lp_max(r, n, w)
            fail |= greedy(ok, n, w)[1] < best
            gap |= val > best + 1e-6
        row["sample"] += 1
        row["greedy_fail"] += fail
        row["lp_gap"] += gap
    return row


def pair_row(n: int, seed: int, sample: int = 250) -> dict:
    """Schnitt der Polytope zweier Matroide: alle Ecken ganzzahlig und gleich den gemeinsamen unabhängigen Mengen? Alle Paare bis n = 4, bei n = 5 eine Stichprobe."""
    rng = random.Random(seed + 200 + n)
    mats = [ok for ok, _ in small_matroids(n)]
    pairs = [(a, b) for a in range(len(mats)) for b in range(len(mats))]
    if n >= 5 and len(pairs) > sample:
        pairs = rng.sample(pairs, sample)
    row = {"n": n, "pairs": len(pairs), "integral": 0, "common": 0}
    for a, b in pairs:
        verts = vertices([mats[a], mats[b]], n)
        common = {tuple(float((m >> e) & 1) for e in range(n)) for m in range(1 << n) if mats[a][m] and mats[b][m]}
        row["integral"] += is_integral(verts)
        row["common"] += verts == common
    return row


def triple_row(n: int) -> dict:
    """Schnitt der Polytope dreier Matroide: wie viele Tripel (alle beschrifteten Matroide auf n Elementen) haben eine gebrochene Ecke?"""
    mats = [ok for ok, _ in small_matroids(n)]
    total = frac = 0
    for trip in itertools.product(range(len(mats)), repeat=3):
        total += 1
        frac += not is_integral(vertices([mats[i] for i in trip], n))
    return {"n": n, "triples": total, "fractional": frac}


def triangle_example() -> dict:
    """Drei Partitionsmatroide auf a, b, c: M1 macht {a, b} abhängig, M2 {a, c}, M3 {b, c}. Gemeinsam unabhängig: ∅, a, b, c; das Polytop hat zusätzlich die Ecke (½, ½, ½)."""
    oks = [partition_table(3, [0, 0, 1], {0: 1, 1: 1}), partition_table(3, [0, 1, 0], {0: 1, 1: 1}), partition_table(3, [1, 0, 0], {0: 1, 1: 1})]
    verts = vertices(oks, 3)
    common = {tuple(float((m >> e) & 1) for e in range(3)) for m in range(8) if all(ok[m] for ok in oks)}
    return {"vertices": sorted(verts), "common": sorted(common), "fractional": sorted(verts - common)}


def plan_series_row(n: int, seeds: int, make_net) -> dict:
    """Pläne mit n Standorten, Seeds 0 bis seeds − 1: Zahl der Pläne, bei denen das Schnitt-LP eine Lücke hat (Wert unter dem Optimum), beim Partitions-LP und beim Rang-LP."""
    row = {"n": n, "plans": seeds, "cut_gap": 0, "partition_gap": 0, "rank_gap": 0, "rounds_max": 0}
    for seed in range(seeds):
        edges, cost = make_net(n, seed)
        opt, _ = kruskal(n, edges, cost)
        gaps = {}
        for kind in ("cut", "partition", "rank"):
            val, _x = tree_lp(n, edges, cost, kind)
            gaps[kind] = val < opt - 1e-6
        row["cut_gap"] += gaps["cut"]
        row["partition_gap"] += gaps["partition"]
        row["rank_gap"] += gaps["rank"]
        if gaps["cut"]:
            row["rounds_max"] = max(row["rounds_max"], len(cutting_plane(n, edges, cost)) - 1)
    return row
