"""Die Netze der Demo: das Leitungsnetz (Plan) und das Handbeispiel K5; dazu die Tabellen des Waldmatroids und seine Rangfunktion."""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

import mpo_constants as C
from mpo_algorithm import graphic_table, rank_table
from mpo_scenario import LETTERS, Instance, make_instance


@dataclass(frozen=True)
class Net:
    key: str
    n: int                      # Zahl der Standorte
    edges: tuple                # ((u, v), …), Position = Nummer der Leitung
    costs: tuple                # Kosten je Leitung (ganze Zahlen)
    labels: tuple               # Name je Leitung
    inst: Instance              # Standorte und Leitungen für die Zeichnung

    @property
    def m(self) -> int:
        return len(self.edges)


def build_net(net: str, n: int, seed: int) -> Net:
    if net == "plan":
        inst = make_instance(n, seed)
        return Net(net, inst.n, tuple((u, w) for u, w, _ in inst.edges), tuple(int(c) for _, _, c in inst.edges), tuple(inst.label(e) for e in range(inst.m)), inst)
    if net == "k5":
        inst = Instance(tuple(C.K5_POINTS), tuple((u, w, c) for (u, w), c in zip(C.K5_EDGES, C.K5_COSTS)))
        return Net(net, 5, tuple(C.K5_EDGES), tuple(C.K5_COSTS), tuple(inst.label(e) for e in range(inst.m)), inst)
    raise ValueError(f"unbekanntes Netz: {net}")


@lru_cache(maxsize=24)
def _cached_net(net: str, n: int, seed: int) -> Net:
    return build_net(net, n, seed)


def get_net(net: str, n: int, seed: int) -> Net:
    """Gleiches Netz für gleiche Eingaben; beim festen K5 zählen n und der Seed nicht."""
    if net != "plan":
        n, seed = 0, 0
    return _cached_net(net, n, seed)


@lru_cache(maxsize=24)
def forest_table(net: str, n: int, seed: int) -> np.ndarray:
    g = get_net(net, n, seed)
    return graphic_table(g.n, list(g.edges))


@lru_cache(maxsize=24)
def forest_rank(net: str, n: int, seed: int) -> np.ndarray:
    g = get_net(net, n, seed)
    return rank_table(forest_table(net, n, seed), g.m)


def node_names(mask: int, n: int) -> str:
    return "{" + ", ".join(LETTERS[v] for v in range(n) if mask >> v & 1) + "}"
