"""Gemeinsame Fixtures: kleine Beispiele, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mpo_algorithm as A  # noqa: E402
import mpo_constants as C  # noqa: E402


@pytest.fixture
def u23():
    """U(2,3): höchstens 2 von 3. Unabhängige Mengen: ∅, a, b, c, ab, ac, bc (7). Rang 2. Polytop: Einheitswürfel ohne die Ecke (1,1,1), geschnitten durch x_a + x_b + x_c ≤ 2:
    7 Ecken, 7 Facetten (x_e ≥ 0 dreimal, x_e ≤ 1 dreimal, x(E) ≤ 2)."""
    ok = A.uniform_table(3, 2)
    return 3, ok, A.rank_table(ok, 3)


@pytest.fixture
def dreieck():
    """Dreieck a, b, c = (0,1), (1,2), (0,2) auf 3 Knoten (Waldmatroid = U(2,3))."""
    edges = [(0, 1), (1, 2), (0, 2)]
    ok = A.graphic_table(3, edges)
    return 3, edges, ok, A.rank_table(ok, 3)


@pytest.fixture
def k5():
    """Handbeispiel K5 aus PLAN-10: Knoten 0 bis 4, Kosten 2, 3, 0, 1, 3, 2, 2, 3, 3, 0; Schnitt-LP 4,5, kleinster Spannbaum 5 (Kanten 03, 34, 01, 02)."""
    return 5, list(C.K5_EDGES), list(C.K5_COSTS)
