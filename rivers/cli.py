"""rivers 命令行入口：河流查询、列表、排名、对比、SVG、练习题与练习纸。"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from typing import List, Optional, Sequence

from rivers.rivers_data import (
    RANK_BY_NAME,
    QuizItem,
    River,
    compare_rivers,
    find_river,
    list_rivers,
    make_quiz,
    rank_rivers,
)
from rivers.svg import build_svg
from rivers.worksheet import generate_worksheet

DEFAULT_QUIZ_COUNT: int = 5
DEFAULT_WORKSHEET_COUNT: int = 8


def _ensure_utf8_console() -> None:
    """尽量把标准输出与标准错误切换为 UTF-8，失败时静默跳过。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def _write_text(path: str, content: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError(
            "写入文件失败：{0}（{1}）".format(path, exc.strerror or exc)
        ) from exc


def _display_width(text: str) -> int:
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def _pad(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return "{0:.2f}".format(value).rstrip("0").rstrip(".")


def _format_row(cells: List[str], widths: List[int]) -> str:
    parts: List[str] = []
    for index, cell in enumerate(cells):
        if index == len(cells) - 1:
            parts.append(cell)
        else:
            parts.append(_pad(cell, widths[index]))
    return "  ".join(parts).rstrip()


def _format_table(headers: List[str], rows: List[List[str]]) -> str:
    all_rows: List[List[str]] = [headers] + rows
    widths: List[int] = []
    for index in range(len(headers)):
        width = 0
        for row in all_rows:
            current = _display_width(row[index])
            if current > width:
                width = current
        widths.append(width)
    lines: List[str] = [_format_row(headers, widths)]
    lines.append(_format_row(["-" * width for width in widths], widths))
    for row in rows:
        lines.append(_format_row(row, widths))
    return "\n".join(lines)


def _format_info(river: River) -> str:
    rows: List[List[str]] = [
        ["名称", river.name],
        ["长度", "{0} km".format(river.length)],
        ["流域面积", "{0} 万 km²".format(_format_number(river.basin_area))],
        ["发源地", river.source],
        ["注入海域", river.mouth],
        ["流经省级行政区", "、".join(river.provinces)],
        ["干流是否跨出国境", "是" if river.international else "否"],
    ]
    label_width = 0
    for row in rows:
        width = _display_width(row[0])
        if width > label_width:
            label_width = width
    lines: List[str] = []
    for row in rows:
        lines.append("{0}：{1}".format(_pad(row[0], label_width), row[1]))
    return "\n".join(lines)


def _format_length_difference(rivers: List[River]) -> str:
    longest = rivers[0]
    shortest = rivers[0]
    for river in rivers[1:]:
        if river.length > longest.length:
            longest = river
        if river.length < shortest.length:
            shortest = river
    difference = longest.length - shortest.length
    if difference == 0:
        return "长度差：{0}与{1}长度相同（0 km）".format(
            longest.name, shortest.name
        )
    return "长度差：{0}比{1}长 {2} km".format(
        longest.name, shortest.name, difference
    )


def _print_quiz(items: List[QuizItem]) -> None:
    print("河流练习题（共 {0} 题）".format(len(items)))
    print("")
    for index, item in enumerate(items, 1):
        print("{0}. [{1}] {2}".format(index, item.kind, item.question))
    print("")
    print("参考答案")
    for index, item in enumerate(items, 1):
        print("{0}. {1}".format(index, item.answer))


def _parse_names(text: str) -> List[str]:
    normalized = text.replace("，", ",")
    names = [part.strip() for part in normalized.split(",") if part.strip()]
    if not names:
        raise ValueError("--names 不能为空，请用逗号分隔河流名称")
    return names


def _run_info(args: argparse.Namespace) -> int:
    print(_format_info(find_river(args.name)))
    return 0


def _run_list(args: argparse.Namespace) -> int:
    rivers = list_rivers(limit=args.limit, min_length=args.min_length)
    rows: List[List[str]] = []
    for river in rivers:
        rows.append(
            [
                str(RANK_BY_NAME[river.name]),
                river.name,
                str(river.length),
                river.mouth,
            ]
        )
    print(_format_table(["名次", "名称", "长度（km）", "注入海域"], rows))
    print("共 {0} 条河流".format(len(rivers)))
    return 0


def _run_rank(args: argparse.Namespace) -> int:
    rivers = rank_rivers(order=args.order, limit=args.limit)
    rows: List[List[str]] = []
    for index, river in enumerate(rivers, 1):
        rows.append([str(index), river.name, str(river.length), river.mouth])
    print(_format_table(["名次", "名称", "长度（km）", "注入海域"], rows))
    print("共 {0} 条河流".format(len(rivers)))
    return 0


def _run_compare(args: argparse.Namespace) -> int:
    rivers = compare_rivers(_parse_names(args.names))
    rows: List[List[str]] = []
    for river in rivers:
        rows.append(
            [
                river.name,
                str(river.length),
                _format_number(river.basin_area),
                river.source,
                river.mouth,
            ]
        )
    print(
        _format_table(
            ["名称", "长度（km）", "流域面积（万 km²）", "发源地", "注入海域"],
            rows,
        )
    )
    print(_format_length_difference(rivers))
    print("共 {0} 条河流参与对比".format(len(rivers)))
    return 0


def _run_svg(args: argparse.Namespace) -> int:
    names = _parse_names(args.names)
    content = build_svg(names)
    _write_text(args.out, content)
    print("已生成条形图：{0}（{1} 条河流）".format(args.out, len(names)))
    return 0


def _run_quiz(args: argparse.Namespace) -> int:
    items = make_quiz(args.count, args.seed)
    _print_quiz(items)
    return 0


def _run_worksheet(args: argparse.Namespace) -> int:
    document = generate_worksheet(args.count, args.seed)
    if args.out is None:
        print(document)
        return 0
    _write_text(args.out, document)
    print("已生成练习纸：{0}（{1} 题）".format(args.out, args.count))
    return 0


def _run_demo() -> int:
    print("=== 河流信息：长江 ===")
    print(_format_info(find_river("长江")))
    print("")
    print("=== 河流对比：长江 vs 黄河 ===")
    rivers = compare_rivers(["长江", "黄河"])
    rows: List[List[str]] = []
    for river in rivers:
        rows.append(
            [
                river.name,
                str(river.length),
                _format_number(river.basin_area),
                river.source,
                river.mouth,
            ]
        )
    print(
        _format_table(
            ["名称", "长度（km）", "流域面积（万 km²）", "发源地", "注入海域"],
            rows,
        )
    )
    print(_format_length_difference(rivers))
    print("")
    print("=== 条形图：长江、黄河、珠江 ===")
    demo_names = ["长江", "黄河", "珠江"]
    _write_text("rivers.svg", build_svg(demo_names))
    print("已生成条形图：rivers.svg（{0} 条河流）".format(len(demo_names)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """构建并返回命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        prog="rivers",
        description="初中地理中国主要河流查询与比较工具：河流信息、长度排名、对比、SVG 条形图与练习纸。",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    info_parser = subparsers.add_parser("info", help="查询单条河流的全部字段信息")
    info_parser.add_argument("--name", required=True, help="河流名称，例如 长江")

    list_parser = subparsers.add_parser("list", help="按长度降序列出河流")
    list_parser.add_argument("--limit", type=int, default=None, help="最多显示的河流条数")
    list_parser.add_argument(
        "--min-length", type=int, default=None, help="只显示长度不小于该值的河流"
    )

    rank_parser = subparsers.add_parser("rank", help="按长度排出名次表")
    rank_parser.add_argument(
        "--order", default="desc", help="排序方式：desc 从长到短，asc 从短到长"
    )
    rank_parser.add_argument("--limit", type=int, default=None, help="最多显示的河流条数")

    compare_parser = subparsers.add_parser("compare", help="对比 2 到 6 条河流")
    compare_parser.add_argument(
        "--names", required=True, help="河流名称，用逗号分隔，例如 长江,黄河"
    )

    svg_parser = subparsers.add_parser("svg", help="生成横向条形图 SVG 文件")
    svg_parser.add_argument(
        "--names", required=True, help="河流名称，用逗号分隔，例如 长江,黄河,珠江"
    )
    svg_parser.add_argument("--out", required=True, help="输出 SVG 文件路径")

    quiz_parser = subparsers.add_parser("quiz", help="生成河流练习题")
    quiz_parser.add_argument(
        "--count", type=int, default=DEFAULT_QUIZ_COUNT, help="题目数量，1 到 50"
    )
    quiz_parser.add_argument("--seed", type=int, default=None, help="随机种子，用于复现题目")

    worksheet_parser = subparsers.add_parser("worksheet", help="生成自包含的 HTML 练习纸")
    worksheet_parser.add_argument(
        "--count", type=int, default=DEFAULT_WORKSHEET_COUNT, help="题目数量，1 到 50"
    )
    worksheet_parser.add_argument(
        "--seed", type=int, default=None, help="随机种子，用于复现练习纸"
    )
    worksheet_parser.add_argument(
        "--out", default=None, help="输出 HTML 文件路径；省略时打印到标准输出"
    )

    subparsers.add_parser("demo", help="运行查询、对比与条形图演示")

    return parser


def _run(args: argparse.Namespace) -> int:
    """根据解析后的参数分发到具体子命令。"""

    if args.command == "info":
        return _run_info(args)
    if args.command == "list":
        return _run_list(args)
    if args.command == "rank":
        return _run_rank(args)
    if args.command == "compare":
        return _run_compare(args)
    if args.command == "svg":
        return _run_svg(args)
    if args.command == "quiz":
        return _run_quiz(args)
    if args.command == "worksheet":
        return _run_worksheet(args)
    if args.command == "demo":
        return _run_demo()
    raise ValueError("未知子命令：{0}".format(args.command))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，返回进程退出码。"""

    _ensure_utf8_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
