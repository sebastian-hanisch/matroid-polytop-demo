"""Szenario: ein Leitungsnetz. Standorte auf einem Plan, mögliche Leitungen mit Kosten. Knoten 0 (A) ist das Depot in der Mitte."""

import random
from dataclasses import dataclass, replace
from math import sqrt

import mpo_constants as C

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(frozen=True)
class Instance:
    points: tuple[tuple[float, float], ...]
    edges: tuple[tuple[int, int, float], ...]  # (u, v, Kosten), u < v, geordnet nach (u, v); der Kantenindex ist die Position

    @property
    def n(self) -> int:
        return len(self.points)

    @property
    def m(self) -> int:
        return len(self.edges)

    def name(self, v: int) -> str:
        return LETTERS[v]

    def label(self, e: int) -> str:
        u, v, _ = self.edges[e]
        return f"{self.name(u)}–{self.name(v)}"


def edge_count(n: int) -> int:
    """So viele mögliche Leitungen hat die Instanz: 2n − 2, aber nie mehr als alle Paare."""
    return min(n * (n - 1) // 2, 2 * n - 2)


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def make_instance(n: int, seed: int, hub: bool = False) -> Instance:
    """Deterministisch aus (n, seed, hub). Der Plan: Depot in der Mitte, n − 1 Standorte zufällig. Mögliche Leitungen: ein kürzestes
    Gerüst (damit die Instanz zusammenhängt) plus die kürzesten übrigen Paare bis zur Kantenzahl. Mit hub kosten Leitungen am Depot 40 %."""
    if not 1 <= n <= len(LETTERS):
        raise ValueError(f"n = {n} außerhalb von 1 bis {len(LETTERS)}")
    rng = random.Random(seed)
    points = [(0.5, 0.5)] + [(rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)) for _ in range(n - 1)]
    pairs = sorted(
        ((sqrt((points[u][0] - points[v][0]) ** 2 + (points[u][1] - points[v][1]) ** 2), u, v) for u in range(n) for v in range(u + 1, n)),
    )
    parent = list(range(n))
    chosen = set()
    for d, u, v in pairs:  # kürzestes Gerüst
        a, b = _find(parent, u), _find(parent, v)
        if a != b:
            parent[a] = b
            chosen.add((u, v))
    for d, u, v in pairs:  # kürzeste übrige Paare
        if len(chosen) >= edge_count(n):
            break
        chosen.add((u, v))
    dist = {(u, v): d for d, u, v in pairs}
    edges = []
    for u, v in sorted(chosen):
        c = dist[(u, v)] * C.COST_SCALE * (C.HUB_FACTOR if hub and u == 0 else 1.0)
        edges.append((u, v, max(1, int(c + 0.5))))
    return Instance(tuple(points), tuple(edges))


def with_costs(inst: Instance, costs) -> Instance:
    """Dieselben Standorte und Leitungen mit anderen Kosten (für Umrechnungen und eigene Kosten)."""
    costs = tuple(costs)
    if len(costs) != inst.m:
        raise ValueError("Kostenliste hat die falsche Länge")
    return replace(inst, edges=tuple((u, v, c) for (u, v, _), c in zip(inst.edges, costs)))
