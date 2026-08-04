"""Vector drawing primitives used to compose the infographics.

Everything is built from reportlab shapes so the same Drawing can be placed
straight into the PDF and rasterised (via PyMuPDF) for the DOCX.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from reportlab.graphics.shapes import Drawing, Group, Line, Polygon, Rect, String
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics

from . import theme

PAGE_W = 468.0  # printable width inside the page margins


def text_width(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text, font, size)


def wrap(text: str, font: str, size: float, max_width: float) -> List[str]:
    lines: List[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if text_width(candidate, font, size) <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def centered_text(group: Group, text: str, cx: float, top: float, width: float,
                  font: str, size: float, color: Color, leading: float | None = None) -> float:
    leading = leading or size * 1.22
    lines = wrap(text, font, size, width)
    y = top - size
    for line in lines:
        group.add(String(cx - text_width(line, font, size) / 2.0, y, line,
                         fontName=font, fontSize=size, fillColor=color))
        y -= leading
    return top - len(lines) * leading


def left_text(group: Group, text: str, x: float, top: float, width: float,
              font: str, size: float, color: Color, leading: float | None = None) -> float:
    leading = leading or size * 1.22
    y = top - size
    for line in wrap(text, font, size, width):
        group.add(String(x, y, line, fontName=font, fontSize=size, fillColor=color))
        y -= leading
    return top - len(wrap(text, font, size, width)) * leading


def box(group: Group, x: float, y: float, w: float, h: float, fill: Color,
        stroke: Color, radius: float = 5, stroke_width: float = 0.9) -> None:
    group.add(Rect(x, y, w, h, rx=radius, ry=radius, fillColor=fill,
                   strokeColor=stroke, strokeWidth=stroke_width))


def arrow_right(group: Group, x: float, y: float, length: float, color: Color) -> None:
    group.add(Line(x, y, x + length - 5, y, strokeColor=color, strokeWidth=1.4))
    group.add(Polygon([x + length - 6, y - 3.4, x + length, y, x + length - 6, y + 3.4],
                      fillColor=color, strokeColor=color))


def arrow_down(group: Group, x: float, y: float, length: float, color: Color) -> None:
    group.add(Line(x, y, x, y - length + 5, strokeColor=color, strokeWidth=1.4))
    group.add(Polygon([x - 3.4, y - length + 6, x, y - length, x + 3.4, y - length + 6],
                      fillColor=color, strokeColor=color))


def _title(drawing: Drawing, group: Group, title: str, caption: str, height: float) -> float:
    """Draw the heading block; returns the y of the next free line."""
    y = height - 13
    group.add(String(0, y, title, fontName=theme.BODY_BOLD, fontSize=11.5, fillColor=theme.INK))
    y -= 4
    if caption:
        y = left_text(group, caption, 0, y, PAGE_W, theme.BODY_FONT, 8.2, theme.MUTED)
    y -= 6
    group.add(Line(0, y, PAGE_W, y, strokeColor=theme.RULE, strokeWidth=0.8))
    return y - 12


def flow(title: str, caption: str, steps: Sequence[Tuple[str, str]],
         color: Color = theme.BLUE, tint: Color = theme.BLUE_TINT) -> Drawing:
    """Left-to-right pipeline: each step is (label, one-line detail)."""
    cols = len(steps)
    gap = 16.0
    w = (PAGE_W - gap * (cols - 1)) / cols

    # Shrink the label font until the longest single word fits inside a box.
    label_size = 8.4
    longest = max((word for label, _ in steps for word in label.split()), key=len)
    while label_size > 6.0 and text_width(longest, theme.BODY_BOLD, label_size) > w - 12:
        label_size -= 0.2

    body_lines = max(len(wrap(d, theme.BODY_FONT, 7.4, w - 12)) for _, d in steps)
    label_lines = max(len(wrap(l, theme.BODY_BOLD, label_size, w - 12)) for l, _ in steps)
    box_h = 16 + label_lines * 10.2 + body_lines * 9.0
    height = box_h + 62
    d = Drawing(PAGE_W, height)
    g = Group()
    top = _title(d, g, title, caption, height)

    y = top - box_h
    for i, (label, detail) in enumerate(steps):
        x = i * (w + gap)
        box(g, x, y, w, box_h, tint, color)
        inner = centered_text(g, label, x + w / 2, y + box_h - 7, w - 12,
                              theme.BODY_BOLD, label_size, color, 10.2)
        centered_text(g, detail, x + w / 2, inner - 2, w - 12,
                      theme.BODY_FONT, 7.4, theme.INK_SOFT, 9.0)
        if i < cols - 1:
            arrow_right(g, x + w + 2, y + box_h / 2, gap - 4, color)
    d.add(g)
    return d


def stack(title: str, caption: str, layers: Sequence[Tuple[str, str]],
          color: Color = theme.SLATE, tint: Color = theme.SLATE_TINT) -> Drawing:
    """Top-to-bottom layered stack: each layer is (label, detail)."""
    label_w = 132.0
    detail_w = PAGE_W - label_w - 14
    heights = []
    for label, detail in layers:
        lines = max(len(wrap(detail, theme.BODY_FONT, 7.8, detail_w - 14)),
                    len(wrap(label, theme.BODY_BOLD, 8.4, label_w - 14)))
        heights.append(max(24.0, 12 + lines * 9.6))
    height = sum(heights) + 6 * (len(layers) - 1) + 58
    d = Drawing(PAGE_W, height)
    g = Group()
    y = _title(d, g, title, caption, height)

    for (label, detail), h in zip(layers, heights):
        y -= h
        box(g, 0, y, label_w, h, color, color)
        box(g, label_w + 6, y, detail_w + 8, h, tint, color)
        centered_text(g, label, label_w / 2, y + h - 5, label_w - 12,
                      theme.BODY_BOLD, 8.4, theme.PAPER, 9.6)
        left_text(g, detail, label_w + 14, y + h - 5, detail_w - 8,
                  theme.BODY_FONT, 7.8, theme.INK_SOFT, 9.6)
        y -= 6
    d.add(g)
    return d


def compare(title: str, caption: str, left_head: str, right_head: str,
            rows: Sequence[Tuple[str, str]]) -> Drawing:
    """Two-column contrast table - the object interviewers love to confuse."""
    col = (PAGE_W - 10) / 2
    heights = []
    for a, b in rows:
        lines = max(len(wrap(a, theme.BODY_FONT, 7.8, col - 16)),
                    len(wrap(b, theme.BODY_FONT, 7.8, col - 16)))
        heights.append(max(22.0, 10 + lines * 9.6))
    height = sum(heights) + 5 * len(rows) + 78
    d = Drawing(PAGE_W, height)
    g = Group()
    y = _title(d, g, title, caption, height)

    head_h = 20.0
    y -= head_h
    box(g, 0, y, col, head_h, theme.BLUE, theme.BLUE)
    box(g, col + 10, y, col, head_h, theme.PURPLE, theme.PURPLE)
    centered_text(g, left_head, col / 2, y + head_h - 5, col - 10, theme.BODY_BOLD, 8.6, theme.PAPER)
    centered_text(g, right_head, col + 10 + col / 2, y + head_h - 5, col - 10,
                  theme.BODY_BOLD, 8.6, theme.PAPER)
    y -= 5

    for (a, b), h in zip(rows, heights):
        y -= h
        box(g, 0, y, col, h, theme.BLUE_TINT, theme.RULE)
        box(g, col + 10, y, col, h, theme.PURPLE_TINT, theme.RULE)
        left_text(g, a, 8, y + h - 4, col - 16, theme.BODY_FONT, 7.8, theme.INK_SOFT, 9.6)
        left_text(g, b, col + 18, y + h - 4, col - 16, theme.BODY_FONT, 7.8, theme.INK_SOFT, 9.6)
        y -= 5
    d.add(g)
    return d


def ladder(title: str, caption: str, rungs: Sequence[Tuple[str, str, str]]) -> Drawing:
    """Growing bars - used for the Foundation -> Architect answer ladder."""
    n = len(rungs)
    gap = 7.0
    widths = [PAGE_W * (0.44 + 0.56 * (i + 1) / n) for i in range(n)]
    heights = []
    for (label, band, detail), w in zip(rungs, widths):
        lines = len(wrap(band, theme.BODY_BOLD, 8.0, w - 100)) + \
            len(wrap(detail, theme.BODY_FONT, 7.5, w - 100))
        heights.append(max(30.0, 11 + lines * 9.2))
    height = sum(heights) + n * gap + 58
    d = Drawing(PAGE_W, height)
    g = Group()
    y = _title(d, g, title, caption, height)

    palette = [theme.TEAL, theme.BLUE, theme.PURPLE, theme.RED]
    tints = [theme.TEAL_TINT, theme.BLUE_TINT, theme.PURPLE_TINT, theme.RED_TINT]
    for i, (label, band, detail) in enumerate(rungs):
        color = palette[i % len(palette)]
        tint = tints[i % len(tints)]
        w = widths[i]
        bar_h = heights[i]
        y -= bar_h
        box(g, 0, y, w, bar_h, tint, color)
        box(g, 0, y, 84, bar_h, color, color)
        centered_text(g, label, 42, y + bar_h / 2 + 4, 78, theme.BODY_BOLD, 8.4, theme.PAPER, 9.4)
        inner = left_text(g, band, 92, y + bar_h - 5, w - 100, theme.BODY_BOLD, 8.0, color, 9.2)
        left_text(g, detail, 92, inner - 1, w - 100, theme.BODY_FONT, 7.5, theme.INK_SOFT, 9.2)
        y -= gap
    d.add(g)
    return d


def matrix(title: str, caption: str, headers: Sequence[str],
           rows: Sequence[Sequence[str]], widths: Sequence[float] | None = None) -> Drawing:
    """Plain data grid for reference cards (ports, conditions, decision tables)."""
    cols = len(headers)
    if widths is None:
        widths = [PAGE_W / cols] * cols
    else:
        total = sum(widths)
        widths = [w / total * PAGE_W for w in widths]
    xs = [sum(widths[:i]) for i in range(cols)]

    heights = []
    for row in rows:
        lines = max(len(wrap(c, theme.BODY_FONT, 7.6, widths[i] - 12)) for i, c in enumerate(row))
        heights.append(max(20.0, 9 + lines * 9.4))
    height = sum(heights) + 22 + 56
    d = Drawing(PAGE_W, height)
    g = Group()
    y = _title(d, g, title, caption, height)

    y -= 22
    box(g, 0, y, PAGE_W, 22, theme.INK, theme.INK, radius=3)
    for i, head in enumerate(headers):
        left_text(g, head, xs[i] + 7, y + 16, widths[i] - 12, theme.BODY_BOLD, 8.0, theme.PAPER, 9.0)

    for r, (row, h) in enumerate(zip(rows, heights)):
        y -= h
        fill = theme.PAPER if r % 2 else theme.SLATE_TINT
        box(g, 0, y, PAGE_W, h, fill, theme.RULE, radius=0, stroke_width=0.5)
        for i, cell in enumerate(row):
            font = theme.BODY_BOLD if i == 0 else theme.BODY_FONT
            color = theme.INK if i == 0 else theme.INK_SOFT
            left_text(g, cell, xs[i] + 7, y + h - 4, widths[i] - 12, font, 7.6, color, 9.4)
    d.add(g)
    return d


def cycle(title: str, caption: str, phases: Sequence[Tuple[str, str]],
          color: Color = theme.TEAL, tint: Color = theme.TEAL_TINT) -> Drawing:
    """Closed loop drawn as two rows with a return arrow underneath."""
    per_row = (len(phases) + 1) // 2
    gap = 14.0
    w = (PAGE_W - gap * (per_row - 1)) / per_row
    cell_h = 0.0
    for label, detail in phases:
        lines = len(wrap(detail, theme.BODY_FONT, 7.3, w - 12)) + \
            len(wrap(label, theme.BODY_BOLD, 8.2, w - 12))
        cell_h = max(cell_h, 14 + lines * 9.4)
    height = cell_h * 2 + 34 + 70
    d = Drawing(PAGE_W, height)
    g = Group()
    top = _title(d, g, title, caption, height)

    rows = [phases[:per_row], phases[per_row:]]
    for r, row in enumerate(rows):
        y = top - cell_h - r * (cell_h + 26)
        for i, (label, detail) in enumerate(row):
            x = i * (w + gap)
            box(g, x, y, w, cell_h, tint, color)
            inner = centered_text(g, label, x + w / 2, y + cell_h - 6, w - 12,
                                  theme.BODY_BOLD, 8.2, color, 9.6)
            centered_text(g, detail, x + w / 2, inner - 1, w - 12,
                          theme.BODY_FONT, 7.3, theme.INK_SOFT, 9.0)
            if i < len(row) - 1:
                arrow_right(g, x + w + 2, y + cell_h / 2, gap - 4, color)
        if r == 0 and len(rows) > 1 and rows[1]:
            arrow_down(g, PAGE_W - w / 2, y - 3, 20, color)
    if len(rows) > 1 and rows[1]:
        y_bottom = top - cell_h * 2 - 26
        g.add(Line(w / 2, y_bottom - 10, PAGE_W - w / 2, y_bottom - 10,
                   strokeColor=color, strokeWidth=1.0, strokeDashArray=[3, 2]))
        g.add(Line(w / 2, y_bottom - 10, w / 2, y_bottom, strokeColor=color,
                   strokeWidth=1.0, strokeDashArray=[3, 2]))
        g.add(Polygon([w / 2 - 3.2, y_bottom - 1, w / 2, y_bottom + 5, w / 2 + 3.2, y_bottom - 1],
                      fillColor=color, strokeColor=color))
    d.add(g)
    return d


def mindmap(title: str, caption: str, hub: str,
            branches: Sequence[Tuple[str, Sequence[str]]],
            color: Color = theme.BLUE, tint: Color = theme.BLUE_TINT) -> Drawing:
    """Two-column mindmap radiating from a central hub label."""
    left = branches[: (len(branches) + 1) // 2]
    right = branches[(len(branches) + 1) // 2 :]
    col_w = (PAGE_W - 120) / 2
    leaf_size = 7.2

    def branch_height(items: Sequence[Tuple[str, Sequence[str]]]) -> float:
        total = 0.0
        for label, leaves in items:
            leaf_lines = sum(max(1, len(wrap(leaf, theme.BODY_FONT, leaf_size, col_w - 28)))
                             for leaf in leaves) or 1
            total += 18 + leaf_lines * 9.0 + 10
        return total

    content_h = max(branch_height(left), branch_height(right), 90.0)
    height = content_h + 78
    d = Drawing(PAGE_W, height)
    g = Group()
    top = _title(d, g, title, caption, height)

    hub_w, hub_h = 108.0, 42.0
    hub_x = (PAGE_W - hub_w) / 2
    hub_y = top - content_h / 2 - hub_h / 2
    box(g, hub_x, hub_y, hub_w, hub_h, color, color, radius=8)
    centered_text(g, hub, hub_x + hub_w / 2, hub_y + hub_h - 8, hub_w - 10,
                  theme.BODY_BOLD, 8.6, theme.PAPER, 10.0)

    palette = [theme.TEAL, theme.BLUE, theme.PURPLE, theme.AMBER, theme.SLATE, theme.RED]
    tints = [theme.TEAL_TINT, theme.BLUE_TINT, theme.PURPLE_TINT, theme.AMBER_TINT,
             theme.SLATE_TINT, theme.RED_TINT]

    def draw_side(items: Sequence[Tuple[str, Sequence[str]]], x: float, toward_right: bool) -> None:
        y = top
        for i, (label, leaves) in enumerate(items):
            c = palette[i % len(palette)]
            t = tints[i % len(tints)]
            leaf_lines = sum(max(1, len(wrap(leaf, theme.BODY_FONT, leaf_size, col_w - 28)))
                             for leaf in leaves) or 1
            box_h = 16 + leaf_lines * 9.0
            y -= box_h
            box(g, x, y, col_w, box_h, t, c, radius=5)
            left_text(g, label, x + 8, y + box_h - 4, col_w - 16, theme.BODY_BOLD, 8.0, c, 9.2)
            ly = y + box_h - 16
            for leaf in leaves:
                ly = left_text(g, f"• {leaf}", x + 10, ly, col_w - 20,
                               theme.BODY_FONT, leaf_size, theme.INK_SOFT, 9.0)
            # connector toward hub
            if toward_right:
                g.add(Line(x + col_w, y + box_h / 2, hub_x, hub_y + hub_h / 2,
                           strokeColor=c, strokeWidth=1.0))
            else:
                g.add(Line(x, y + box_h / 2, hub_x + hub_w, hub_y + hub_h / 2,
                           strokeColor=c, strokeWidth=1.0))
            y -= 10

    draw_side(left, 0, True)
    draw_side(right, PAGE_W - col_w, False)
    d.add(g)
    return d
