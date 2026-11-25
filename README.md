# rivers
[![CI](https://github.com/eastyou/rivers/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/rivers/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

`rivers` 是一个纯标准库实现的命令行工具，面向初中地理师生，提供中国主要河流查询、长度排名、对比、SVG 条形图与可打印练习纸。

## 项目简介

河流是初中地理“中国的自然环境”部分的核心内容，长江、黄河等主要河流的长度、发源地、注入海域与流经省份经常出现在课堂提问和考试中。`rivers` 把 18 条中国主要河流整理成结构化数据，用一条命令即可查到全部字段，省去反复翻书核对的时间。

项目同时关注“比较”和“出题”两个课堂场景：`compare` 能把 2 到 6 条河流放在同一张表里对比并标出长度差，`svg` 能直接生成可插入课件的横向条形图，`quiz` 与 `worksheet` 则能按固定随机种子生成可复现的练习题与 HTML 练习纸。所有数值采用初中地理教学中的常用概数，便于学生记忆和手工计算。整个项目只依赖 Python 标准库，兼容 Python 3.9 及以上版本。

## 特性

- 内置 18 条中国主要河流，覆盖长江、黄河、珠江、黑龙江、雅鲁藏布江、塔里木河等高频考点。
- 每条河流包含名称、长度、流域面积、发源地、注入海域、流经省级行政区、是否跨出国境七个字段。
- `info` 输出全部字段，省级行政区用顿号连接，未知河流会提示全部可用名称。
- `list` 与 `rank` 支持按长度升序或降序排列，并可用数量上限与最短长度过滤。
- `compare` 支持 2 到 6 条河流对比，自动计算并标注最长与最短河流的长度差。
- `svg` 与 `worksheet` 分别生成自包含的 SVG 条形图和 HTML 练习纸，`quiz` 同一随机种子完全复现。

## 安装

从 GitHub 直接安装：

```bash
pip install git+https://github.com/eastyou/rivers.git
```

在本地源码目录以可编辑模式安装：

```bash
git clone https://github.com/eastyou/rivers.git
cd rivers
pip install -e .
```

不安装也可以在源码目录直接运行：

```bash
cd rivers
python3 -m rivers --help
```

## 使用

### info

按名称查询单条河流的全部字段，名称首尾空白会被忽略。

```bash
rivers info --name 长江
```

```text
名称            ：长江
长度            ：6300 km
流域面积        ：180 万 km²
发源地          ：唐古拉山脉各拉丹冬雪山
注入海域        ：东海
流经省级行政区  ：青海、西藏、四川、云南、重庆、湖北、湖南、江西、安徽、江苏、上海
干流是否跨出国境：否
```

### list

按长度降序列出河流，可用 `--limit` 限制条数、`--min-length` 过滤短河。

```bash
rivers list --limit 5 --min-length 1000
```

```text
名次  名称      长度（km）  注入海域
----  --------  ----------  ----------------------
1     长江      6300        东海
2     黄河      5464        渤海
3     黑龙江    4370        鄂霍次克海（鞑靼海峡）
4     珠江      2320        南海
5     塔里木河  2179        台特玛湖
共 5 条河流
```

### rank

按长度排出名次表，`--order desc` 从长到短，`--order asc` 从短到长。

```bash
rivers rank --order desc --limit 5
```

```text
名次  名称      长度（km）  注入海域
----  --------  ----------  ----------------------
1     长江      6300        东海
2     黄河      5464        渤海
3     黑龙江    4370        鄂霍次克海（鞑靼海峡）
4     珠江      2320        南海
5     塔里木河  2179        台特玛湖
共 5 条河流
```

### compare

对比 2 到 6 条河流，输出长度、流域面积、发源地与注入海域，并标注长度差。

```bash
rivers compare --names 长江,黄河
```

```text
名称  长度（km）  流域面积（万 km²）  发源地                  注入海域
----  ----------  ------------------  ----------------------  --------
长江  6300        180                 唐古拉山脉各拉丹冬雪山  东海
黄河  5464        75.2                青海省巴颜喀拉山脉      渤海
长度差：长江比黄河长 836 km
共 2 条河流参与对比
```

### svg

生成横向条形图 SVG，包含坐标轴、网格线、条形、名称与数值标注，以及可被读屏软件识别的 `<title>`。

```bash
rivers svg --names 长江,黄河,珠江 --out rivers.svg
```

```text
已生成条形图：rivers.svg（3 条河流）
```

### quiz

生成三类练习题：最长或第 N 长的河、某河注入哪里、某河发源于哪里。题目在前，参考答案统一列在最后，同一 seed 输出完全一致。

```bash
rivers quiz --count 5 --seed 2026
```

```text
河流练习题（共 5 题）

1. [最长/第N长] 中国长度排第 6 的河流是哪一条？
2. [注入海域] 「黑龙江」注入哪里？
3. [发源地] 「长江」发源于哪里？
4. [最长/第N长] 中国长度排第 2 的河流是哪一条？
5. [注入海域] 「渭河」注入哪里？

参考答案
1. 澜沧江（2139 km）
2. 鄂霍次克海（鞑靼海峡）
3. 唐古拉山脉各拉丹冬雪山
4. 黄河（5464 km）
5. 黄河
```

### worksheet

生成自包含 HTML 练习纸，混合填表题与三类简答题，答案放在末尾的 `<details>` 折叠区。省略 `--out` 时打印到标准输出。

```bash
rivers worksheet --count 8 --seed 2026 --out worksheet.html
```

```text
已生成练习纸：worksheet.html（8 题）
```

### demo

一次展示河流查询、对比与条形图写入结果。

```bash
rivers demo
```

```text
=== 河流信息：长江 ===
名称            ：长江
长度            ：6300 km
流域面积        ：180 万 km²
发源地          ：唐古拉山脉各拉丹冬雪山
注入海域        ：东海
流经省级行政区  ：青海、西藏、四川、云南、重庆、湖北、湖南、江西、安徽、江苏、上海
干流是否跨出国境：否

=== 河流对比：长江 vs 黄河 ===
名称  长度（km）  流域面积（万 km²）  发源地                  注入海域
----  ----------  ------------------  ----------------------  --------
长江  6300        180                 唐古拉山脉各拉丹冬雪山  东海
黄河  5464        75.2                青海省巴颜喀拉山脉      渤海
长度差：长江比黄河长 836 km

=== 条形图：长江、黄河、珠江 ===
已生成条形图：rivers.svg（3 条河流）
```

### 参数

| 参数 | 说明 |
| --- | --- |
| `--name` | `info` 子命令：河流名称，例如 `长江`，首尾空白会被忽略 |
| `--limit` | `list` 与 `rank` 子命令：最多显示的河流条数，必须大于 0 |
| `--min-length` | `list` 子命令：只显示长度不小于该值的河流，范围 1 到 10000 |
| `--order` | `rank` 子命令：`desc` 从长到短，`asc` 从短到长，默认 `desc` |
| `--names` | `compare` 与 `svg` 子命令：河流名称，用逗号分隔；`compare` 需要 2 到 6 条 |
| `--out` | `svg` 子命令：输出 SVG 路径，必填；`worksheet` 子命令：输出 HTML 路径，可省略 |
| `--count` | `quiz` 与 `worksheet` 子命令：题目数量，1 到 50，默认分别为 5 和 8 |
| `--seed` | `quiz` 与 `worksheet` 子命令：随机种子，用于复现同一套题 |
| `-h, --help` | 显示帮助并退出，退出码为 0 |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 命令执行成功 |
| 2 | 参数错误或业务校验失败，错误信息写入标准错误 |

## 作为库使用

```python
from rivers import build_svg, compare_rivers, find_river, list_rivers, make_quiz

river = find_river("长江")
print(river.name, river.length, river.mouth)  # 长江 6300 东海

print([item.name for item in list_rivers(limit=3)])  # ['长江', '黄河', '黑龙江']

print([item.name for item in compare_rivers(["长江", "黄河"])])  # ['长江', '黄河']

quiz = make_quiz(1, seed=2026)[0]
print(quiz.question)  # 中国长度排第 6 的河流是哪一条？
print(quiz.answer)  # 澜沧江（2139 km）

print(build_svg(["长江"]).startswith("<svg"))  # True
```

## 开发与测试

在项目根目录运行全部单元测试：

```bash
python3 -m unittest discover -s tests -v
```

当前共 102 个用例，覆盖数据完整性、河流查询、列表过滤、排名升降序、对比数量与长度差、SVG 结构与可解析性、练习题复现、练习纸结构、文件写入失败处理以及 CLI 各子命令与退出码。CI 在 Ubuntu 上覆盖 Python 3.9、3.10、3.11、3.12、3.13，并执行 `python -m rivers --help` 冒烟检查。

## License

[MIT](LICENSE) © 2026 eastyou
