"""把河流长度渲染为横向条形图 SVG。

只用字符串拼接生成 SVG，不依赖 xml.etree，便于在任何环境直接输出文件。
"""

from __future__ import annotations

import html
from typing import List, Optional, Sequence, Tuple

from rivers.rivers_data import MAX_COMPARE, River, resolve_rivers

WIDTH: int = 760
TOP: int = 72
ROW_HEIGHT: int = 48
BAR_HEIGHT: int = 28
LEFT: int = 140
RIGHT: int = 100
PLOT_WIDTH: int = WIDTH - LEFT - RIGHT

_PALETTE: Tuple[str, ...] = (
    "#3b6ea5",
    "#2f8f6b",
    "#c26b3a",
    "#8a5fb0",
    "#c04b5a",
    "#4a8fa8",
)


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _nice_step(max_value: int) -> int:
    for step in (2000, 1000, 500, 200, 100, 50):
        if max_value / step >= 4:
            return step
    return 50


def _bar_width(length: int, max_length: int) -> int:
    return int(round(length / float(max_length) * PLOT_WIDTH))


def build_svg(names: Sequence[str], title: Optional[str] = None) -> str:
    """根据河流名称生成横向条形图 SVG 文本。"""

    if title is not None and not isinstance(title, str):
        raise TypeError("title 必须是字符串或 None")
    rivers: List[River] = resolve_rivers(names, 1, MAX_COMPARE)
    if title is None:
        chart_title = "中国主要河流长度对比"
    else:
        chart_title = title.strip() or "中国主要河流长度对比"

    height = TOP + len(rivers) * ROW_HEIGHT + 56
    baseline = TOP + len(rivers) * ROW_HEIGHT + 8
    max_length = max(river.length for river in rivers)

    lines: List[str] = []
    lines.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="{0}" height="{1}" '
        'viewBox="0 0 {0} {1}" role="img" aria-label="{2}">'.format(
            WIDTH, height, _escape(chart_title)
        )
    )
    lines.append("  <title>{0}</title>".format(_escape(chart_title)))
    lines.append(
        '  <rect x="0" y="0" width="{0}" height="{1}" fill="#ffffff"/>'.format(
            WIDTH, height
        )
    )

    step = _nice_step(max_length)
    tick = 0
    ticks: List[int] = []
    while tick <= max_length:
        ticks.append(tick)
        tick += step

    for value in ticks:
        x = LEFT + int(round(value / float(max_length) * PLOT_WIDTH))
        lines.append(
            '  <line x1="{0}" y1="{1}" x2="{0}" y2="{2}" '
            'stroke="#d9e2ec" stroke-width="1"/>'.format(x, TOP - 12, baseline)
        )
        lines.append(
            '  <text x="{0}" y="{1}" font-size="12" fill="#52606d" '
            'text-anchor="middle">{2}</text>'.format(x, baseline + 20, value)
        )

    lines.append(
        '  <line x1="{0}" y1="{1}" x2="{2}" y2="{1}" stroke="#52606d" '
        'stroke-width="1.5"/>'.format(LEFT, baseline, LEFT + PLOT_WIDTH)
    )
    lines.append(
        '  <line x1="{0}" y1="{1}" x2="{0}" y2="{2}" stroke="#52606d" '
        'stroke-width="1.5"/>'.format(LEFT, TOP - 12, baseline)
    )
    lines.append(
        '  <text x="{0}" y="{1}" font-size="13" fill="#1f3a5f" '
        'text-anchor="middle">长度（km）</text>'.format(
            LEFT + PLOT_WIDTH // 2, height - 12
        )
    )

    for index, river in enumerate(rivers):
        bar_x = LEFT
        bar_y = TOP + index * ROW_HEIGHT + (ROW_HEIGHT - BAR_HEIGHT) // 2
        width = _bar_width(river.length, max_length)
        color = _PALETTE[index % len(_PALETTE)]
        center_y = bar_y + BAR_HEIGHT // 2 + 5
        lines.append(
            '  <g class="bar">'
            '<rect x="{0}" y="{1}" width="{2}" height="{3}" rx="4" '
            'fill="{4}"/>'.format(bar_x, bar_y, width, BAR_HEIGHT, color)
        )
        lines.append(
            '  <text x="{0}" y="{1}" font-size="14" fill="#1f2933" '
            'text-anchor="end">{2}</text>'.format(
                LEFT - 12, center_y, _escape(river.name)
            )
        )
        lines.append(
            '  <text x="{0}" y="{1}" font-size="13" fill="#1f2933" '
            'text-anchor="start">{2} km</text></g>'.format(
                LEFT + width + 8, center_y, river.length
            )
        )

    lines.append("</svg>")
    return "\n".join(lines)
