"""
Defect 02 — IF/ELIF 边界破坏 + IS_OP 退化为 COMPARE_OP ==
================================================================
触发区域类型：IF (if/elif/else) + IS_OP (is None)
根因初判：
    core/cfg/region_analyzer.py `_identify_if_regions` 的 elif
    合并逻辑把紧随 `if A:` 之后的 `elif B:` 的条件片段错误
    并入 `if A:` 条件，生成 `(A) == B` 形式的 Compare；
    同时 core/cfg/region_ast_generator.py `_generate_if` 把
    POP_JUMP_IF_NONE/POP_JUMP_IF_NOT_NONE (IS_OP) 重建为
    COMPARE_OP `== None`，改变了 `is` 与 `==` 的语义。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL quote
    POP_JUMP_FORWARD_IF_NOT_NONE to <elif>     # quote is None
    LOAD_GLOBAL is_trade
    POP_JUMP_FORWARD_IF_FALSE to <elif>
    <if-body>
  <elif>:
    LOAD_GLOBAL frequency
    CONTAINS_OP 0                              # frequency in OVER_WEEK_FREQUENCY
    POP_JUMP_FORWARD_IF_FALSE to <else>
    LOAD_GLOBAL query_date
    POP_JUMP_FORWARD_IF_NOT_NONE to <else>     # query_date is None
    <elif-body>

反编译产物（错误）：
    if (quote == None and is_trade) == OVER_WEEK_FREQUENCY:
        quote = Quote()
    elif frequency in OVER_WEEK_FREQUENCY and query_date == None:
        query_date = datetime.now()
期望产物：
    if quote is None and is_trade:
        quote = Quote()
    elif frequency in OVER_WEEK_FREQUENCY and query_date is None:
        query_date = datetime.now()

验证：python pycdc.py <this>.pyc  # 观察 if 条件被改写为 == 与错位合并
"""
def get_quote():
    global quote
    if quote is None and is_trade:
        quote = Quote()
    elif frequency in OVER_WEEK_FREQUENCY and query_date is None:
        query_date = datetime.now()
    return quote
