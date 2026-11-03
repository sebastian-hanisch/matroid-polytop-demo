"""Plotly-Abbildungen. Alle ebenen Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mpo_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _frame(fig, lo=-0.05, hi=1.05):
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)


def _lines(inst, edge_ids):
    xs, ys = [], []
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        xs += [inst.points[u][0], inst.points[v][0], None]
        ys += [inst.points[u][1], inst.points[v][1], None]
    return xs, ys


def build_net(net, full=(), frac=(), edge_text=None, node_mark=None, tree=(), height=430):
    """Das Netz mit einer LP-Lösung: full = Leitungen mit x = 1 (dick, blaugrün), frac = gebrochene (dick, orange, mit Beschriftung aus edge_text), übrige dünn grau.
    tree: kleinster Spannbaum als gestrichelte Hilfslinie. node_mark: Standorte einer verletzten Knotenmenge (rot), sonst Depot orange und die übrigen blau."""
    inst = net.inst
    fig = go.Figure()
    shown = set(full) | set(frac)
    rest = [e for e in range(inst.m) if e not in shown]
    if rest:
        xs, ys = _lines(inst, rest)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OTHER, width=2), name="x = 0", hoverinfo="skip"))
    if tree:
        xs, ys = _lines(inst, list(tree))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="rgba(240,163,10,0.55)", width=14), name="kleinster Spannbaum", hoverinfo="skip"))
    if full:
        xs, ys = _lines(inst, list(full))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_TREE, width=6), name="x = 1", hoverinfo="skip"))
    if frac:
        xs, ys = _lines(inst, list(frac))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_HALF, width=6, dash="dot"), name="gebrochen", hoverinfo="skip"))
    if edge_text:
        ids = sorted(edge_text)
        fig.add_trace(go.Scatter(
            x=[(inst.points[inst.edges[e][0]][0] + inst.points[inst.edges[e][1]][0]) / 2 for e in ids], y=[(inst.points[inst.edges[e][0]][1] + inst.points[inst.edges[e][1]][1]) / 2 for e in ids],
            mode="text", text=[edge_text[e] for e in ids], textfont=dict(size=13), hoverinfo="skip", showlegend=False))
    mark = set(node_mark or ())
    colors = [C.COLOR_VIOLATED if v in mark else (C.COLOR_DEPOT if v == 0 else C.COLOR_NODE) for v in range(inst.n)]
    fig.add_trace(go.Scatter(
        x=[p[0] for p in inst.points], y=[p[1] for p in inst.points], mode="markers+text", text=[inst.name(v) for v in range(inst.n)], textposition="top center", textfont=dict(size=14),
        marker=dict(size=16, color=colors, line=dict(color="white", width=1.5)), hovertemplate="%{text}<extra></extra>", showlegend=False))
    _frame(fig)
    return _base(fig, height)


def build_polytope(mat: dict, vertices, edges, greedy_vertex=None, height=420):
    """Das Polytop eines kleinen Matroids in 3D. Koordinaten: (x_a, x_b, x_c); beim Basenpolytop mit vier Elementen folgt x_d aus x_a + x_b + x_c + x_d = r.
    vertices: Bitmasken der Ecken, edges: Paare von Ecken, greedy_vertex: Maske der Greedy-Ecke (rot)."""
    n = mat["n"]
    labels = mat["labels"]

    def pt(mask):
        return [(mask >> e) & 1 for e in range(3)]

    pts = {v: pt(v) for v in vertices}
    fig = go.Figure()
    xs, ys, zs = zip(*[pts[v] for v in vertices])
    fig.add_trace(go.Mesh3d(x=list(xs), y=list(ys), z=list(zs), alphahull=0, color=C.COLOR_FACE, opacity=0.35, hoverinfo="skip", name="Polytop", showlegend=False))
    ex, ey, ez = [], [], []
    for a, b in edges:
        ex += [pts[a][0], pts[b][0], None]
        ey += [pts[a][1], pts[b][1], None]
        ez += [pts[a][2], pts[b][2], None]
    fig.add_trace(go.Scatter3d(x=ex, y=ey, z=ez, mode="lines", line=dict(color=C.COLOR_VERTEX, width=5), name="Kanten", hoverinfo="skip"))
    names = ["".join(labels[e] for e in range(n) if v >> e & 1) or "∅" for v in vertices]
    colors = [C.COLOR_GREEDY if v == greedy_vertex else C.COLOR_VERTEX for v in vertices]
    sizes = [10 if v == greedy_vertex else 6 for v in vertices]
    fig.add_trace(go.Scatter3d(x=list(xs), y=list(ys), z=list(zs), mode="markers+text", text=names, textposition="top center", marker=dict(size=sizes, color=colors),
                               hovertemplate="%{text}<extra></extra>", name="Ecken", showlegend=False))
    fig.update_layout(height=height, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.05),
                      scene=dict(xaxis_title=f"x_{labels[0]}", yaxis_title=f"x_{labels[1]}", zaxis_title=f"x_{labels[2]}", aspectmode="cube"))
    return fig


def build_bar_chart(categories, values, colors, x_title, y_title, hover, height=300):
    """Balken; hover ist eine Formatzeichenfolge mit %{x} und %{y}."""
    fig = go.Figure(go.Bar(x=list(categories), y=list(values), marker_color=list(colors), hovertemplate=hover + "<extra></extra>"))
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)
