"""
Defect 02 (R1 残留) — IF/ELIF 边界破坏 + IS_OP 退化为 `== None`（R2 仍复现，且 `not in` 同步退化为 `in`）
================================================================
关联 R1 repro：repro_02_if_elif_boundary_is_none（R1 未修复，留待 R2）。

R2 复现状态：**复现**。
  quotation.pyc::get_quote line 87 `if quote == None and is_trade:`
  quotation.pyc::get_history line 779 `elif frequency in OVER_WEEK_FREQUENCY and query_date == None:`
  （原 `not in OVER_WEEK_FREQUENCY` 退化为 `in`，`is None` 退化为 `== None`）
  quotation.pyc::date_convert line 2131 `if report_types == None and month_temp == 1:`

触发区域类型：IF (if/elif/else) + IS_OP (is None) + CONTAINS_OP (not in)
根因初判：
    (a) `core/cfg/region_ast_generator.py::_generate_if` 仍把
        `POP_JUMP_IF_NONE` / `POP_JUMP_IF_NOT_NONE`（IS_OP）重建为
        `COMPARE_OP == None` / `!= None`，改变 `is` 与 `==` 语义。
    (b) `POP_JUMP_FORWARD_IF_TRUE`（`not in` 的反向跳转）被误读为正向
        `in`，导致 `not in X` 退化为 `in X`。
    违反「每块唯一归属」：IS_OP / CONTAINS_OP 反向跳转的条件块归属错位。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL quote
    POP_JUMP_FORWARD_IF_NOT_NONE to <elif>     # quote is None  → 误重建为 == None
    LOAD_GLOBAL is_trade
    POP_JUMP_FORWARD_IF_FALSE to <elif>
    <if-body>
  <elif>:
    LOAD_GLOBAL frequency
    CONTAINS_OP 0                              # frequency not in OVER_WEEK_FREQUENCY
    POP_JUMP_FORWARD_IF_FALSE to <else>
    LOAD_GLOBAL query_date
    POP_JUMP_FORWARD_IF_NOT_NONE to <else>     # query_date is None → == None

R2 反编译产物（错误）：
    if quote == None and is_trade:
        ...
    elif frequency in OVER_WEEK_FREQUENCY and query_date == None:
        ...
期望产物：
    if quote is None and is_trade:
        ...
    elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:
        ...

验证：python pycdc.py <this>.pyc  # 观察 is None → == None，not in → in
"""
def get_quote():
    global quote
    if quote is None and is_trade:
        quote = Quote()
    elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:
        query_date = datetime.now()
    return quote
