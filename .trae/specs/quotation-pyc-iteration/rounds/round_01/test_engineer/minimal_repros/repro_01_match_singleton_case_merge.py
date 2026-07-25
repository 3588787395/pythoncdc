"""
Defect 01 — MATCH region: MatchSingleton case 模式合并失败
================================================================
触发区域类型：MATCH (match/case 语句)
根因初判：
    core/cfg/region_ast_generator.py `_generate_match` +
    core/cfg/pattern_parser.py 的 MatchOr 重建逻辑。
    当 match 语句同时包含 `case None:`(MatchSingleton) 与
    `case str():`(MatchClass) / `case _:`(MatchAs) 时，
    `_mr_finalize_match_region` (region_analyzer.py L8168) 把
    多个 case 错误合并为一个 MatchOr 模式，导致：
      1) MatchSingleton 字典被当作表达式节点传入
         code_generator._generate_expression (L3360)，
         触发 "Unknown expression type: MatchSingleton" 警告；
      2) MatchClass 字典与 ASTName 对象的 repr 直接拼入
         源码 (`<core.ast_nodes.ASTName object at 0x...>`)；
      3) case body 丢失，match 块未正确终止。

最小字节码模式（Python 3.11，case None + case str() + case _）：
    RESUME
    LOAD_FAST x
    COPY 1                   # subject 保留
    LOAD_CONST None
    COMPARE_OP is            # case None: IS_OP
    POP_JUMP_FORWARD_IF_FALSE to <case_str>
    <case None body>
    JUMP_FORWARD to <end>
  <case_str>:
    COPY 1
    LOAD_GLOBAL str
    LOAD_CONST 0             # class pattern positional count
    MATCH_CLASS              # case str():
    POP_JUMP_FORWARD_IF_FALSE to <case_wild>
    <case str body>
  <case_wild>:
    POP_TOP                  # case _:
    <case _ body>

反编译产物（错误）：
    match x:
        case None | {'type': 'MatchClass', 'cls': <...ASTName...>, 'patterns': []} | x:
            date = time.strftime('%Y-%m-%d')
            return date
期望产物：
    match x:
        case None:
            return 'none'
        case str():
            pass
        case _:
            date = date.replace('-', '')

验证：python -c "import py_compile; py_compile.compile(__file__)" &&
      python pycdc.py <this>.pyc 2>&1 | grep -E "MatchSingleton|case"
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
