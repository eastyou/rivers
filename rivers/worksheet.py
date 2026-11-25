"""生成自包含的中国主要河流 HTML 练习纸。

练习纸由填表题与三类简答题组成，答案统一放在文档末尾的 details 折叠区，
打印时不会直接暴露答案。
"""

from __future__ import annotations

import html
import random
from typing import List, Optional, Tuple

from rivers.rivers_data import (
    MAX_QUIZ,
    MIN_QUIZ,
    RIVERS_RANKED,
    QuizItem,
    River,
    make_quiz,
)

_STYLE: str = """
body { font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
       max-width: 900px; margin: 0 auto; padding: 28px; color: #1f2933;
       background: #ffffff; line-height: 1.7; }
h1 { font-size: 24px; margin: 0 0 8px 0; text-align: center; }
h2 { font-size: 18px; margin: 28px 0 10px 0; border-left: 4px solid #3b6ea5;
     padding-left: 10px; color: #1f3a5f; }
.meta { margin: 4px 0; color: #52606d; font-size: 14px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 20px 0; }
th, td { border: 1px solid #9aa5b1; padding: 7px 8px; text-align: center; }
th { background: #eef2f7; font-weight: 600; }
.blank { color: #52606d; letter-spacing: 2px; }
ol { margin: 8px 0 18px 0; padding-left: 26px; }
li { margin: 7px 0; }
details { margin-top: 26px; border: 1px solid #9aa5b1; border-radius: 6px;
          padding: 12px 16px; background: #f8fafc; }
summary { cursor: pointer; font-weight: 600; color: #1f3a5f; }
@media print { body { padding: 0; } details { background: #ffffff; } }
""".strip()


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def _format_number(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return "{0:.2f}".format(value).rstrip("0").rstrip(".")


def _validate_count(count: int) -> None:
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("count 必须是整数")
    if count < MIN_QUIZ or count > MAX_QUIZ:
        raise ValueError("count 必须在 {0} 到 {1} 之间".format(MIN_QUIZ, MAX_QUIZ))


def _validate_seed(seed: Optional[int]) -> None:
    if seed is None:
        return
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed 必须是整数或 None")


def _split_counts(count: int) -> Tuple[int, int]:
    """把总题数拆成填表题与简答题数量，两者之和等于 count。"""

    if count <= 1:
        return 0, count
    table_count = max(1, count // 4)
    if table_count >= count:
        table_count = count - 1
    return table_count, count - table_count


def _table_section(rivers: List[River], rng: random.Random) -> Tuple[str, List[str]]:
    rows: List[str] = []
    answers: List[str] = []
    for river in rivers:
        values: List[str] = [
            river.name,
            str(river.length),
            _format_number(river.basin_area),
            river.mouth,
        ]
        hidden = rng.sample((1, 2, 3), 2)
        cells: List[str] = []
        for position, value in enumerate(values):
            if position in hidden:
                cells.append('<td class="blank">______</td>')
            else:
                cells.append("<td>{0}</td>".format(_escape(value)))
        rows.append('<tr class="q">{0}</tr>'.format("".join(cells)))
        answers.append(
            "{0}：长度 {1} km，流域面积 {2} 万 km²，注入 {3}".format(
                _escape(river.name),
                river.length,
                _format_number(river.basin_area),
                _escape(river.mouth),
            )
        )
    table = (
        "<table>\n"
        "<thead><tr><th>河流名称</th><th>长度（km）</th>"
        "<th>流域面积（万 km²）</th><th>注入海域</th></tr></thead>\n"
        "<tbody>\n{0}\n</tbody>\n</table>"
    ).format("\n".join(rows))
    return table, answers


def _quiz_section(items: List[QuizItem]) -> Tuple[str, List[str]]:
    questions: List[str] = []
    answers: List[str] = []
    for item in items:
        questions.append(
            '<li class="q">[{0}] {1}</li>'.format(
                _escape(item.kind), _escape(item.question)
            )
        )
        answers.append(_escape(item.answer))
    body = '<ol class="questions">\n{0}\n</ol>'.format("\n".join(questions))
    return body, answers


def generate_worksheet(count: int, seed: Optional[int] = None) -> str:
    """生成 UTF-8 编码的完整 HTML 练习纸文本。"""

    _validate_count(count)
    _validate_seed(seed)

    table_count, quiz_count = _split_counts(count)
    rng = random.Random(seed)
    pool: List[River] = list(RIVERS_RANKED)
    rng.shuffle(pool)
    table_rivers = pool[:table_count]

    table_html = ""
    table_answers: List[str] = []
    if table_count > 0:
        table_html, table_answers = _table_section(table_rivers, rng)

    quiz_items = make_quiz(quiz_count, seed)
    quiz_html, quiz_answers = _quiz_section(quiz_items)

    answers: List[str] = []
    for answer in table_answers:
        answers.append(answer)
    for answer in quiz_answers:
        answers.append(answer)

    lines: List[str] = []
    lines.append("<!DOCTYPE html>")
    lines.append('<html lang="zh-CN">')
    lines.append("<head>")
    lines.append('<meta charset="utf-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    lines.append("<title>中国主要河流练习纸</title>")
    lines.append("<style>")
    lines.append(_STYLE)
    lines.append("</style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append("<h1>中国主要河流练习纸</h1>")
    lines.append(
        '<p class="meta">姓名：__________　班级：__________　日期：__________</p>'
    )
    lines.append(
        '<p class="meta">题目数量：{0}　随机种子：{1}</p>'.format(
            count, "无" if seed is None else str(seed)
        )
    )

    section_index = 0
    if table_count > 0:
        section_index += 1
        lines.append(
            "<h2>{0}、填表题</h2>".format("一二三四五六七八九十"[section_index - 1])
        )
        lines.append("<p>根据已有信息，补全表中空白处。</p>")
        lines.append(table_html)

    section_index += 1
    lines.append(
        "<h2>{0}、简答题</h2>".format("一二三四五六七八九十"[section_index - 1])
    )
    lines.append("<p>回答下列问题，注意河流长度、发源地与注入海域。</p>")
    lines.append(quiz_html)

    lines.append("<details>")
    lines.append("<summary>参考答案</summary>")
    lines.append('<ol class="answers">')
    for answer in answers:
        lines.append("<li>{0}</li>".format(answer))
    lines.append("</ol>")
    lines.append("</details>")

    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines)
