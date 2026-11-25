"""中国主要河流数据与查询函数。

所有数值采用初中地理教学中的常用概数，便于课堂讲解与学生记忆。
长度单位为千米（km），流域面积单位为万平方千米（万 km²）。
黑龙江长度 4370 km 为全河长度，中国境内河段约 3474 km。
雅鲁藏布江、澜沧江、怒江的长度与流域面积均指中国境内部分。
"""

from __future__ import annotations

import random
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple

MIN_LENGTH: int = 1
MAX_LENGTH: int = 10000
MIN_COMPARE: int = 2
MAX_COMPARE: int = 6
ORDERS: Tuple[str, ...] = ("desc", "asc")
MIN_QUIZ: int = 1
MAX_QUIZ: int = 50
KINDS: Tuple[str, ...] = ("最长/第N长", "注入海域", "发源地")


class River(NamedTuple):
    """单条河流的不可变数据记录。"""

    name: str
    length: int
    basin_area: float
    source: str
    mouth: str
    provinces: Tuple[str, ...]
    international: bool


class QuizItem(NamedTuple):
    """一道练习题及其参考答案。"""

    kind: str
    question: str
    answer: str


_RAW_RIVERS: Tuple[Tuple[str, int, float, str, str, Tuple[str, ...], bool], ...] = (
    (
        "长江",
        6300,
        180.0,
        "唐古拉山脉各拉丹冬雪山",
        "东海",
        ("青海", "西藏", "四川", "云南", "重庆", "湖北", "湖南", "江西", "安徽", "江苏", "上海"),
        False,
    ),
    (
        "黄河",
        5464,
        75.2,
        "青海省巴颜喀拉山脉",
        "渤海",
        ("青海", "四川", "甘肃", "宁夏", "内蒙古", "陕西", "山西", "河南", "山东"),
        False,
    ),
    (
        "黑龙江",
        4370,
        185.6,
        "蒙古国肯特山脉",
        "鄂霍次克海（鞑靼海峡）",
        ("内蒙古", "黑龙江"),
        True,
    ),
    (
        "珠江",
        2320,
        45.4,
        "云南省马雄山",
        "南海",
        ("云南", "贵州", "广西", "广东"),
        False,
    ),
    (
        "塔里木河",
        2179,
        102.0,
        "天山山脉与昆仑山脉（叶尔羌河源出喀喇昆仑山）",
        "台特玛湖",
        ("新疆",),
        False,
    ),
    (
        "澜沧江",
        2139,
        16.7,
        "青海省唐古拉山脉",
        "南海（经湄公河）",
        ("青海", "西藏", "云南"),
        True,
    ),
    (
        "雅鲁藏布江",
        2057,
        24.0,
        "喜马拉雅山脉北麓杰马央宗冰川",
        "孟加拉湾（经布拉马普特拉河）",
        ("西藏",),
        True,
    ),
    (
        "怒江",
        2013,
        13.6,
        "青藏高原唐古拉山脉南麓",
        "安达曼海（经萨尔温江）",
        ("西藏", "云南"),
        True,
    ),
    (
        "松花江",
        1927,
        55.7,
        "长白山天池",
        "黑龙江",
        ("吉林", "黑龙江"),
        False,
    ),
    (
        "汉江",
        1577,
        15.9,
        "陕西省秦岭南麓",
        "长江",
        ("陕西", "湖北"),
        False,
    ),
    (
        "辽河",
        1345,
        21.9,
        "河北省七老图山脉",
        "渤海",
        ("河北", "内蒙古", "吉林", "辽宁"),
        False,
    ),
    (
        "淮河",
        1000,
        27.0,
        "河南省桐柏山",
        "洪泽湖",
        ("河南", "安徽", "江苏"),
        False,
    ),
    (
        "湘江",
        856,
        9.46,
        "广西壮族自治区海洋山",
        "洞庭湖",
        ("广西", "湖南"),
        False,
    ),
    (
        "渭河",
        818,
        13.5,
        "甘肃省鸟鼠山",
        "黄河",
        ("甘肃", "陕西"),
        False,
    ),
    (
        "赣江",
        766,
        8.16,
        "江西省武夷山脉",
        "鄱阳湖",
        ("江西",),
        False,
    ),
    (
        "岷江",
        735,
        13.6,
        "四川省岷山南麓",
        "长江",
        ("四川",),
        False,
    ),
    (
        "钱塘江",
        605,
        5.56,
        "安徽省黄山",
        "东海",
        ("安徽", "浙江"),
        False,
    ),
    (
        "闽江",
        577,
        6.1,
        "福建省武夷山脉",
        "东海",
        ("福建",),
        False,
    ),
)

RIVERS: Tuple[River, ...] = tuple(River(*row) for row in _RAW_RIVERS)

RIVERS_BY_NAME: Dict[str, River] = {river.name: river for river in RIVERS}

RIVERS_RANKED: Tuple[River, ...] = tuple(
    sorted(RIVERS, key=lambda river: -river.length)
)

RANK_BY_NAME: Dict[str, int] = {
    river.name: index for index, river in enumerate(RIVERS_RANKED, 1)
}


def _validate_count(count: int, minimum: int, maximum: int, label: str) -> None:
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError("{0} 必须是整数".format(label))
    if count < minimum or count > maximum:
        raise ValueError(
            "{0} 必须在 {1} 到 {2} 之间".format(label, minimum, maximum)
        )


def _validate_limit(limit: Optional[int]) -> None:
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise TypeError("limit 必须是整数")
    if limit <= 0:
        raise ValueError("limit 必须大于 0")


def _validate_min_length(min_length: Optional[int]) -> None:
    if min_length is None:
        return
    if isinstance(min_length, bool) or not isinstance(min_length, int):
        raise TypeError("min_length 必须是整数")
    if min_length < MIN_LENGTH or min_length > MAX_LENGTH:
        raise ValueError(
            "min_length 必须在 {0} 到 {1} 之间".format(MIN_LENGTH, MAX_LENGTH)
        )


def _validate_seed(seed: Optional[int]) -> None:
    if seed is None:
        return
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed 必须是整数或 None")


def river_names() -> List[str]:
    """按长度降序返回全部河流名称。"""

    return [river.name for river in RIVERS_RANKED]


def find_river(name: str) -> River:
    """按名称查找河流，忽略首尾空白；找不到时抛出 ValueError。"""

    if not isinstance(name, str):
        raise TypeError("河流名称必须是字符串")
    key = name.strip()
    if not key:
        raise ValueError("河流名称不能为空")
    river = RIVERS_BY_NAME.get(key)
    if river is None:
        raise ValueError(
            "未找到河流：{0}。可用名称：{1}".format(key, "、".join(river_names()))
        )
    return river


def list_rivers(
    limit: Optional[int] = None, min_length: Optional[int] = None
) -> List[River]:
    """按长度降序列出河流，可按数量上限与最短长度过滤。"""

    _validate_limit(limit)
    _validate_min_length(min_length)
    selected: List[River] = []
    for river in RIVERS_RANKED:
        if min_length is not None and river.length < min_length:
            continue
        selected.append(river)
    if limit is not None:
        selected = selected[:limit]
    return selected


def rank_rivers(order: str = "desc", limit: Optional[int] = None) -> List[River]:
    """按长度排序返回河流；order 只能是 desc 或 asc。"""

    if not isinstance(order, str):
        raise TypeError("order 必须是字符串")
    if order not in ORDERS:
        raise ValueError("order 只能是 desc 或 asc")
    _validate_limit(limit)
    ordered = list(RIVERS_RANKED)
    if order == "asc":
        ordered.reverse()
    if limit is not None:
        ordered = ordered[:limit]
    return ordered


def resolve_rivers(
    names: Sequence[str], minimum: int, maximum: int
) -> List[River]:
    """把名称序列解析为河流列表，并校验数量范围。"""

    if isinstance(names, str):
        raise TypeError("names 必须是河流名称序列，而不是单个字符串")
    try:
        raw_names = list(names)
    except TypeError:
        raise TypeError("names 必须是河流名称序列") from None
    if len(raw_names) < minimum or len(raw_names) > maximum:
        raise ValueError(
            "河流数量必须在 {0} 到 {1} 条之间，当前为 {2} 条".format(
                minimum, maximum, len(raw_names)
            )
        )
    rivers: List[River] = []
    for item in raw_names:
        if not isinstance(item, str):
            raise TypeError("河流名称必须是字符串")
        rivers.append(find_river(item))
    return rivers


def compare_rivers(names: Sequence[str]) -> List[River]:
    """解析 2 到 6 条河流用于对比，保持输入顺序。"""

    return resolve_rivers(names, MIN_COMPARE, MAX_COMPARE)


def make_quiz(count: int, seed: Optional[int] = None) -> List[QuizItem]:
    """生成可复现的河流练习题，相同 seed 输出完全一致。"""

    _validate_count(count, MIN_QUIZ, MAX_QUIZ, "count")
    _validate_seed(seed)

    rng = random.Random(seed)
    pool: List[River] = list(RIVERS_RANKED)
    rng.shuffle(pool)

    items: List[QuizItem] = []
    for index in range(count):
        kind = KINDS[index % len(KINDS)]
        river = pool[index % len(pool)]
        if kind == KINDS[0]:
            rank = RANK_BY_NAME[river.name]
            if rank == 1:
                question = "中国最长的河流是哪一条？"
            else:
                question = "中国长度排第 {0} 的河流是哪一条？".format(rank)
            answer = "{0}（{1} km）".format(river.name, river.length)
        elif kind == KINDS[1]:
            question = "「{0}」注入哪里？".format(river.name)
            answer = river.mouth
        else:
            question = "「{0}」发源于哪里？".format(river.name)
            answer = river.source
        items.append(QuizItem(kind, question, answer))
    return items
