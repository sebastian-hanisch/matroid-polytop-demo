"""PDF-Export des aktuellen Beispiels (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import mpo_constants as C
from mpo_evaluation import Settings, dual_view, lp_view, net_of, num, round_text, rounds_view, verdict_dual, verdict_lp, verdict_rounds

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "×": "x", "≈": "~", "∖": "\\", "∩": "n", "∪": "u", "∨": "v", "∅": "{}", "½": "1/2",
            "₁": "1", "₂": "2", "²": "2", "Σ": "Summe", "δ": "d", "∈": "in", "⊆": "<=", "∥": "||"}


def _s(text) -> str:
    out = str(text).replace("**", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings) -> bytes:
    net = net_of(s)
    v = lp_view(s)
    rounds = rounds_view(s)
    dv = dual_view(s)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Matroid-Polytop: Spannbaum-LP"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    plan = C.NET_NAMES[s.net] + (f", {s.n} Standorte, Plan-Seed {s.seed}" if s.net == "plan" else "")
    pdf.multi_cell(0, 5, _s(f"{plan}; {net.m} Leitungen. Formulierung: {C.FORM_NAMES[s.form]}. Kleinster Spannbaum: {num(v['opt'])}; LP-Wert: {num(v['value'])}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Ergebnis der gewählten Formulierung"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _s(verdict_lp(s, v)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Schnittebenenlauf (Start: Schnittbedingungen)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for i in range(len(rounds)):
        pdf.multi_cell(0, 5, _s(round_text(net, rounds, i)[1]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.multi_cell(0, 5, _s(verdict_rounds(net, v, rounds)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Greedy und Dual"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _s(verdict_dual(net, dv)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: matroid-polytop-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
