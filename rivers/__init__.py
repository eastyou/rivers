"""中国主要河流查询与比较工具。"""

from __future__ import annotations

from rivers.rivers_data import (
    River,
    compare_rivers,
    find_river,
    list_rivers,
    make_quiz,
    rank_rivers,
)
from rivers.svg import build_svg
from rivers.worksheet import generate_worksheet

__version__: str = "0.1.0"

__all__ = [
    "River",
    "find_river",
    "list_rivers",
    "rank_rivers",
    "compare_rivers",
    "build_svg",
    "make_quiz",
    "generate_worksheet",
]
