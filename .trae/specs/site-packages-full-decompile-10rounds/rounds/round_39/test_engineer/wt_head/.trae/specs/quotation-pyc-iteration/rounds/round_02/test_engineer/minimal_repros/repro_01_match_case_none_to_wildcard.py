"""
Defect 01 (R1 残留) — MATCH: `case None` / `case str()` 被发射为 `case _` (wildcard)，pattern 保真失败
================================================================
关联 R1 repro：repro_01_match_singleton_case_merge（R1 已消除 MatchSingleton 警告、
解除 P0 阻塞；残留 case 模式保真问题，留待 R2）。

R2 复现状态：**复现**。
  quotation.pyc::process / get_str_data 等多处 match 块在 R2 产物中均被发射为
  `match date: case _: date = time.strftime('%Y-%m-%d')`，原 `case None:` 与
  `case str():` 的模式信息完全丢失，全部塌缩为 wildcard。

触发区域类型：MATCH (match/case 语句)
根因初判：
    R1 修复在 `core/cfg/region_analyzer.py::_mr_finalize_match_region` 把
    MatchSingleton 从 MatchOr 中拆出并按 case 边界归约后，case pattern 的
    重建路径（`core/cfg/pattern_parser.py` / `region_ast_generator._generate_match`）
    未能把 `COMPARE_OP is None`（IS_OP）的 case 重建为 `MatchSingleton(None)`、
    把 `MATCH_CLASS str` 重建为 `MatchClass(str, [])`，而是统一回退到
    `MatchAs(pattern=None)`（即 `case _`）。
    违反「嵌套即抽象节点」：IS_OP/MATCH_CLASS 应作为模式节点，不应回退 wildcard。

最小字节码模式（Python 3.11，case None + case str() + case _）：
    RESUME
    LOAD_FAST date
    COPY 1
    LOAD_CONST None
    COMPARE_OP is                 # case None: IS_OP
    POP_JUMP_FORWARD_IF_FALSE to <case_str>
    <case None body>
    JUMP_FORWARD to <end>
  <case_str>:
    COPY 1
    LOAD_GLOBAL str
    LOAD_CONST 0
    MATCH_CLASS                   # case str():
    POP_JUMP_FORWARD_IF_FALSE to <case_wild>
    <case str body>
  <case_wild>:
    POP_TOP                       # case _:
    <case _ body>

R2 反编译产物（错误，pattern 全塌缩为 wildcard）：
    match date:
        case _:
            date = time.strftime('%Y-%m-%d')
期望产物：
    match date:
        case None:
            return 'none'
        case str():
            pass
        case _:
            date = date.replace('-', '')

验证：python pycdc.py <this>.pyc  # 观察 case None / case str() 是否塌缩为 case _
"""
def process(date, isVaildDate, change_date_format):
    if date and isVaildDate(str(date)):
        date = change_date_format(date)
    match date:
        case None:
            return 'none'
        case str():
            pass
        case _:
            date = date.replace('-', '')
    return date
