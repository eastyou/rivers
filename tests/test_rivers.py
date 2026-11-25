"""rivers 项目的单元测试。"""

from __future__ import annotations

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from typing import List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import rivers
from rivers.cli import _write_text, main
from rivers.rivers_data import (
    KINDS,
    MAX_LENGTH,
    RANK_BY_NAME,
    RIVERS,
    RIVERS_BY_NAME,
    RIVERS_RANKED,
    compare_rivers,
    find_river,
    list_rivers,
    make_quiz,
    rank_rivers,
)
from rivers.svg import build_svg
from rivers.worksheet import generate_worksheet

REQUIRED_NAMES: Tuple[str, ...] = (
    "长江",
    "黄河",
    "珠江",
    "黑龙江",
    "松花江",
    "雅鲁藏布江",
    "澜沧江",
    "怒江",
    "汉江",
    "辽河",
    "淮河",
    "湘江",
    "赣江",
    "闽江",
    "塔里木河",
)


class TagCollector(HTMLParser):
    """收集 HTML 或 SVG 片段中的标签名与文本。"""

    def __init__(self) -> None:
        HTMLParser.__init__(self)
        self.tags: List[str] = []
        self.texts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.tags.append(tag)

    def handle_startendtag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.tags.append(tag)

    def handle_data(self, data: str) -> None:
        self.texts.append(data)


def parse_markup(text: str) -> TagCollector:
    collector = TagCollector()
    collector.feed(text)
    collector.close()
    return collector


def run_cli(args: List[str]) -> Tuple[int, str, str]:
    """在当前进程中运行 CLI，捕获输出并返回退出码。"""

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = 0
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = main(args)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    return code, stdout.getvalue(), stderr.getvalue()


class RiverDataTests(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(rivers.__version__, "0.1.0")

    def test_river_count(self) -> None:
        self.assertGreaterEqual(len(RIVERS), 15)

    def test_names_unique(self) -> None:
        names = [river.name for river in RIVERS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), len(RIVERS_BY_NAME))

    def test_required_names_present(self) -> None:
        for name in REQUIRED_NAMES:
            with self.subTest(name=name):
                self.assertIn(name, RIVERS_BY_NAME)

    def test_changjiang_length(self) -> None:
        river = RIVERS_BY_NAME["长江"]
        self.assertEqual(river.length, 6300)
        self.assertEqual(river.basin_area, 180.0)
        self.assertFalse(river.international)

    def test_huanghe_length(self) -> None:
        river = RIVERS_BY_NAME["黄河"]
        self.assertEqual(river.length, 5464)
        self.assertEqual(river.mouth, "渤海")

    def test_heilongjiang_length(self) -> None:
        river = RIVERS_BY_NAME["黑龙江"]
        self.assertEqual(river.length, 4370)
        self.assertTrue(river.international)

    def test_yaluzangbu_length(self) -> None:
        river = RIVERS_BY_NAME["雅鲁藏布江"]
        self.assertEqual(river.length, 2057)
        self.assertTrue(river.international)

    def test_all_lengths_valid(self) -> None:
        for river in RIVERS:
            with self.subTest(name=river.name):
                self.assertIsInstance(river.length, int)
                self.assertNotIsInstance(river.length, bool)
                self.assertGreater(river.length, 0)
                self.assertLessEqual(river.length, MAX_LENGTH)

    def test_basin_area_positive(self) -> None:
        for river in RIVERS:
            with self.subTest(name=river.name):
                self.assertIsInstance(river.basin_area, float)
                self.assertGreater(river.basin_area, 0)

    def test_provinces_valid(self) -> None:
        for river in RIVERS:
            with self.subTest(name=river.name):
                self.assertIsInstance(river.provinces, tuple)
                self.assertTrue(river.provinces)
                self.assertEqual(len(river.provinces), len(set(river.provinces)))
                for province in river.provinces:
                    self.assertTrue(province.strip())

    def test_international_flags(self) -> None:
        for river in RIVERS:
            self.assertIsInstance(river.international, bool)
        for name in ("黑龙江", "澜沧江", "怒江", "雅鲁藏布江"):
            with self.subTest(name=name):
                self.assertTrue(RIVERS_BY_NAME[name].international)
        for name in ("长江", "黄河", "珠江", "塔里木河"):
            with self.subTest(name=name):
                self.assertFalse(RIVERS_BY_NAME[name].international)

    def test_source_and_mouth_non_empty(self) -> None:
        for river in RIVERS:
            with self.subTest(name=river.name):
                self.assertTrue(river.source)
                self.assertTrue(river.mouth)

    def test_ranked_sorted_desc(self) -> None:
        lengths = [river.length for river in RIVERS_RANKED]
        self.assertEqual(lengths, sorted(lengths, reverse=True))
        self.assertEqual(RIVERS_RANKED[0].name, "长江")
        self.assertEqual(RIVERS_RANKED[-1].name, "闽江")

    def test_rank_index_consistent(self) -> None:
        for index, river in enumerate(RIVERS_RANKED, 1):
            self.assertEqual(RANK_BY_NAME[river.name], index)

    def test_tarim_inland_lake(self) -> None:
        self.assertIn("湖", RIVERS_BY_NAME["塔里木河"].mouth)
        self.assertIn("新疆", RIVERS_BY_NAME["塔里木河"].provinces)


class FindRiverTests(unittest.TestCase):
    def test_find_changjiang(self) -> None:
        river = find_river("长江")
        self.assertEqual(river.name, "长江")
        self.assertEqual(river.length, 6300)

    def test_find_strips_whitespace(self) -> None:
        self.assertEqual(find_river("  黄河  ").name, "黄河")

    def test_find_unknown_raises(self) -> None:
        with self.assertRaises(ValueError) as context:
            find_river("亚马逊河")
        self.assertIn("未找到河流", str(context.exception))
        self.assertIn("可用名称", str(context.exception))
        self.assertIn("长江", str(context.exception))

    def test_find_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            find_river("   ")

    def test_find_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            find_river(123)  # type: ignore[arg-type]


class ListRiversTests(unittest.TestCase):
    def test_default_lists_all(self) -> None:
        result = list_rivers()
        self.assertEqual(len(result), len(RIVERS))
        self.assertEqual(result[0].name, "长江")
        self.assertEqual(result[-1].name, "闽江")

    def test_sorted_desc(self) -> None:
        lengths = [river.length for river in list_rivers()]
        self.assertEqual(lengths, sorted(lengths, reverse=True))

    def test_limit(self) -> None:
        result = list_rivers(limit=3)
        self.assertEqual([river.name for river in result], ["长江", "黄河", "黑龙江"])

    def test_limit_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            list_rivers(limit=0)

    def test_limit_negative_raises(self) -> None:
        with self.assertRaises(ValueError):
            list_rivers(limit=-5)

    def test_limit_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            list_rivers(limit=True)

    def test_min_length(self) -> None:
        result = list_rivers(min_length=3000)
        self.assertTrue(result)
        for river in result:
            self.assertGreaterEqual(river.length, 3000)
        names = [river.name for river in result]
        self.assertIn("黑龙江", names)
        self.assertNotIn("珠江", names)

    def test_min_length_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            list_rivers(min_length=0)

    def test_min_length_too_large_raises(self) -> None:
        with self.assertRaises(ValueError):
            list_rivers(min_length=MAX_LENGTH + 1)

    def test_limit_exceeds_count(self) -> None:
        self.assertEqual(len(list_rivers(limit=999)), len(RIVERS))

    def test_combined_filters(self) -> None:
        result = list_rivers(limit=2, min_length=1000)
        self.assertEqual([river.name for river in result], ["长江", "黄河"])


class RankRiversTests(unittest.TestCase):
    def test_order_desc(self) -> None:
        result = rank_rivers("desc")
        self.assertEqual(result[0].name, "长江")
        self.assertEqual(result[-1].name, "闽江")

    def test_order_asc(self) -> None:
        result = rank_rivers("asc")
        self.assertEqual(result[0].name, "闽江")
        self.assertEqual(result[-1].name, "长江")

    def test_default_order_is_desc(self) -> None:
        self.assertEqual(rank_rivers(), rank_rivers("desc"))

    def test_limit(self) -> None:
        result = rank_rivers("desc", limit=4)
        self.assertEqual(
            [river.name for river in result], ["长江", "黄河", "黑龙江", "珠江"]
        )

    def test_invalid_order_raises(self) -> None:
        with self.assertRaises(ValueError) as context:
            rank_rivers("up")
        self.assertIn("desc", str(context.exception))

    def test_order_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            rank_rivers(1)  # type: ignore[arg-type]

    def test_limit_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            rank_rivers("desc", limit=0)


class CompareRiversTests(unittest.TestCase):
    def test_two_rivers(self) -> None:
        result = compare_rivers(["长江", "黄河"])
        self.assertEqual([river.name for river in result], ["长江", "黄河"])

    def test_preserves_input_order(self) -> None:
        result = compare_rivers(["黄河", "长江"])
        self.assertEqual([river.name for river in result], ["黄河", "长江"])

    def test_one_river_raises(self) -> None:
        with self.assertRaises(ValueError):
            compare_rivers(["长江"])

    def test_seven_rivers_raises(self) -> None:
        names = [river.name for river in RIVERS_RANKED[:7]]
        with self.assertRaises(ValueError):
            compare_rivers(names)

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            compare_rivers([])

    def test_unknown_river_raises(self) -> None:
        with self.assertRaises(ValueError):
            compare_rivers(["长江", "不存在的河"])

    def test_length_difference(self) -> None:
        result = compare_rivers(["长江", "黄河"])
        self.assertEqual(result[0].length - result[1].length, 836)

    def test_single_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            compare_rivers("长江")  # type: ignore[arg-type]

    def test_non_string_item_raises(self) -> None:
        with self.assertRaises(TypeError):
            compare_rivers(["长江", 3])  # type: ignore[list-item]


class SvgTests(unittest.TestCase):
    def test_starts_with_svg(self) -> None:
        self.assertTrue(build_svg(["长江", "黄河"]).startswith("<svg"))

    def test_contains_title(self) -> None:
        svg = build_svg(["长江"])
        self.assertIn("<title>", svg)
        self.assertIn("</title>", svg)

    def test_contains_names(self) -> None:
        svg = build_svg(["长江", "黄河", "珠江"])
        for name in ("长江", "黄河", "珠江"):
            with self.subTest(name=name):
                self.assertIn(name, svg)

    def test_contains_lengths(self) -> None:
        svg = build_svg(["长江", "黄河"])
        self.assertIn("6300 km", svg)
        self.assertIn("5464 km", svg)

    def test_parses_with_html_parser(self) -> None:
        svg = build_svg(["长江", "黄河"])
        collector = parse_markup(svg)
        self.assertIn("svg", collector.tags)
        self.assertIn("rect", collector.tags)
        self.assertIn("text", collector.tags)

    def test_bar_count(self) -> None:
        svg = build_svg(["长江", "黄河", "珠江"])
        self.assertEqual(svg.count('class="bar"'), 3)

    def test_contains_axes(self) -> None:
        svg = build_svg(["长江", "黄河"])
        self.assertIn("<line", svg)
        self.assertIn('stroke="#52606d"', svg)

    def test_unknown_river_raises(self) -> None:
        with self.assertRaises(ValueError):
            build_svg(["长江", "不存在的河"])

    def test_too_many_rivers_raises(self) -> None:
        names = [river.name for river in RIVERS_RANKED[:7]]
        with self.assertRaises(ValueError):
            build_svg(names)

    def test_single_river(self) -> None:
        svg = build_svg(["闽江"])
        self.assertTrue(svg.startswith("<svg"))
        self.assertIn("闽江", svg)

    def test_title_is_escaped(self) -> None:
        svg = build_svg(["长江"], title="A<B&\"C\"")
        self.assertIn("&lt;", svg)
        self.assertIn("&amp;", svg)
        self.assertNotIn("A<B", svg)

    def test_title_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            build_svg(["长江"], title=3)  # type: ignore[arg-type]


class QuizTests(unittest.TestCase):
    def test_count(self) -> None:
        self.assertEqual(len(make_quiz(5, 2026)), 5)
        self.assertEqual(len(make_quiz(50, 2026)), 50)

    def test_reproducible(self) -> None:
        self.assertEqual(make_quiz(6, 2026), make_quiz(6, 2026))

    def test_different_seed_differs(self) -> None:
        self.assertNotEqual(make_quiz(6, 1), make_quiz(6, 2))

    def test_kinds_cover_all(self) -> None:
        items = make_quiz(6, 2026)
        kinds = set(item.kind for item in items)
        self.assertEqual(kinds, set(KINDS))

    def test_answers_non_empty(self) -> None:
        for item in make_quiz(10, 2026):
            with self.subTest(question=item.question):
                self.assertTrue(item.question)
                self.assertTrue(item.answer)

    def test_count_zero_raises(self) -> None:
        with self.assertRaises(ValueError):
            make_quiz(0)

    def test_count_too_large_raises(self) -> None:
        with self.assertRaises(ValueError):
            make_quiz(51)

    def test_seed_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            make_quiz(3, "2026")  # type: ignore[arg-type]

    def test_rank_answer_consistent(self) -> None:
        items = make_quiz(30, 2026)
        ranking_items = [item for item in items if item.kind == KINDS[0]]
        self.assertTrue(ranking_items)
        for item in ranking_items:
            if "最长" in item.question:
                expected = RIVERS_RANKED[0].name
            else:
                match = re.search(r"第 (\d+) 的", item.question)
                self.assertIsNotNone(match)
                rank = int(match.group(1))  # type: ignore[union-attr]
                expected = RIVERS_RANKED[rank - 1].name
            self.assertTrue(item.answer.startswith(expected))


class WorksheetTests(unittest.TestCase):
    def test_doctype(self) -> None:
        document = generate_worksheet(8, 2026)
        self.assertTrue(document.startswith("<!DOCTYPE html>"))

    def test_title_and_style(self) -> None:
        document = generate_worksheet(8, 2026)
        self.assertIn("<title>", document)
        self.assertIn("<style>", document)

    def test_details_collapsed_answers(self) -> None:
        document = generate_worksheet(8, 2026)
        self.assertIn("<details>", document)
        self.assertIn("</details>", document)
        self.assertIn("参考答案", document)

    def test_question_count(self) -> None:
        document = generate_worksheet(8, 2026)
        self.assertEqual(document.count('class="q"'), 8)

    def test_reproducible(self) -> None:
        self.assertEqual(
            generate_worksheet(8, 2026), generate_worksheet(8, 2026)
        )

    def test_contains_table(self) -> None:
        document = generate_worksheet(8, 2026)
        self.assertIn("<table>", document)
        self.assertIn("流域面积", document)

    def test_contains_answers(self) -> None:
        document = generate_worksheet(8, 2026)
        collector = parse_markup(document)
        self.assertIn("details", collector.tags)
        self.assertTrue(any("km" in text for text in collector.texts))

    def test_count_one(self) -> None:
        document = generate_worksheet(1, 2026)
        self.assertEqual(document.count('class="q"'), 1)
        self.assertNotIn("<table>", document)

    def test_invalid_count_raises(self) -> None:
        for count in (0, 51):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    generate_worksheet(count)

    def test_seed_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            generate_worksheet(8, "2026")  # type: ignore[arg-type]


class CliTests(unittest.TestCase):
    def test_help_exit_zero(self) -> None:
        code, stdout, _ = run_cli(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("usage: rivers", stdout)

    def test_info_success(self) -> None:
        code, stdout, _ = run_cli(["info", "--name", "长江"])
        self.assertEqual(code, 0)
        self.assertIn("6300 km", stdout)
        self.assertIn("青海、西藏", stdout)
        self.assertIn("干流是否跨出国境", stdout)

    def test_info_unknown_exit_two(self) -> None:
        code, _, stderr = run_cli(["info", "--name", "亚马逊河"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)
        self.assertIn("未找到河流", stderr)

    def test_list_success(self) -> None:
        code, stdout, _ = run_cli(["list", "--limit", "3"])
        self.assertEqual(code, 0)
        self.assertIn("长江", stdout)
        self.assertIn("共 3 条河流", stdout)

    def test_list_filters(self) -> None:
        code, stdout, _ = run_cli(
            ["list", "--min-length", "3000", "--limit", "2"]
        )
        self.assertEqual(code, 0)
        self.assertIn("长江", stdout)
        self.assertIn("黄河", stdout)
        self.assertNotIn("珠江", stdout)
        self.assertIn("共 2 条河流", stdout)

    def test_list_bad_limit_exit_two(self) -> None:
        code, _, stderr = run_cli(["list", "--limit", "0"])
        self.assertEqual(code, 2)
        self.assertIn("limit 必须大于 0", stderr)

    def test_rank_desc(self) -> None:
        code, stdout, _ = run_cli(["rank", "--limit", "2"])
        self.assertEqual(code, 0)
        self.assertIn("长江", stdout)
        self.assertIn("黄河", stdout)

    def test_rank_asc(self) -> None:
        code, stdout, _ = run_cli(["rank", "--order", "asc", "--limit", "3"])
        self.assertEqual(code, 0)
        self.assertLess(stdout.index("闽江"), stdout.index("钱塘江"))

    def test_rank_bad_order_exit_two(self) -> None:
        code, _, stderr = run_cli(["rank", "--order", "up"])
        self.assertEqual(code, 2)
        self.assertIn("order 只能是 desc 或 asc", stderr)

    def test_compare_success(self) -> None:
        code, stdout, _ = run_cli(["compare", "--names", "长江,黄河"])
        self.assertEqual(code, 0)
        self.assertIn("长度（km）", stdout)
        self.assertIn("长江比黄河长 836 km", stdout)

    def test_compare_one_exit_two(self) -> None:
        code, _, stderr = run_cli(["compare", "--names", "长江"])
        self.assertEqual(code, 2)
        self.assertIn("河流数量必须在 2 到 6 条之间", stderr)

    def test_compare_seven_exit_two(self) -> None:
        names = ",".join(river.name for river in RIVERS_RANKED[:7])
        code, _, stderr = run_cli(["compare", "--names", names])
        self.assertEqual(code, 2)
        self.assertIn("河流数量必须在 2 到 6 条之间", stderr)

    def test_svg_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "rivers.svg")
            code, stdout, _ = run_cli(
                ["svg", "--names", "长江,黄河,珠江", "--out", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成条形图", stdout)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertTrue(content.startswith("<svg"))

    def test_svg_too_many_exit_two(self) -> None:
        names = ",".join(river.name for river in RIVERS_RANKED[:7])
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "rivers.svg")
            code, _, stderr = run_cli(["svg", "--names", names, "--out", path])
            self.assertEqual(code, 2)
            self.assertIn("河流数量必须在", stderr)

    def test_quiz_success(self) -> None:
        code, stdout, _ = run_cli(["quiz", "--count", "5", "--seed", "2026"])
        self.assertEqual(code, 0)
        self.assertIn("河流练习题（共 5 题）", stdout)
        self.assertIn("参考答案", stdout)

    def test_quiz_reproducible(self) -> None:
        first = run_cli(["quiz", "--count", "6", "--seed", "2026"])[1]
        second = run_cli(["quiz", "--count", "6", "--seed", "2026"])[1]
        self.assertEqual(first, second)

    def test_quiz_bad_count_exit_two(self) -> None:
        code, _, stderr = run_cli(["quiz", "--count", "0"])
        self.assertEqual(code, 2)
        self.assertIn("count 必须在", stderr)

    def test_worksheet_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "worksheet.html")
            code, stdout, _ = run_cli(
                ["worksheet", "--count", "8", "--seed", "2026", "--out", path]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成练习纸", stdout)
            with open(path, "r", encoding="utf-8") as handle:
                content = handle.read()
            self.assertTrue(content.startswith("<!DOCTYPE html>"))
            self.assertEqual(content.count('class="q"'), 8)

    def test_demo_success(self) -> None:
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            os.chdir(directory)
            try:
                code, stdout, _ = run_cli(["demo"])
                self.assertEqual(code, 0)
                self.assertIn("长江", stdout)
                self.assertIn("已生成条形图：rivers.svg", stdout)
                self.assertTrue(os.path.exists(os.path.join(directory, "rivers.svg")))
            finally:
                os.chdir(previous)

    def test_unknown_command_exit_two(self) -> None:
        code, _, _ = run_cli(["unknown"])
        self.assertEqual(code, 2)

    def test_no_command_exit_two(self) -> None:
        code, _, _ = run_cli([])
        self.assertEqual(code, 2)

    def test_write_text_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "sample.txt")
            _write_text(path, "河流")
            with open(path, "r", encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "河流")

    def test_write_text_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "missing", "sample.txt")
            with self.assertRaises(ValueError):
                _write_text(path, "河流")


if __name__ == "__main__":
    unittest.main()
