"""
Defect 06 (R1 残留，已演化) — IF/BOOLOP + IfExp：函数实参位置的 IfExp 被误读为 `and`，赋值体塌缩为 docstring
================================================================
关联 R1 repro：repro_06_if_boolop_and_decompose（R1：`if A and B:` 被拆为嵌套 `if A: if B:`）。

R2 复现状态：**复现（形态演化，且更严重）**。
  R1 表现：`if A and B:` → 嵌套 `if A: if B:`，else 语义改变
  R2 表现（quotation.pyc::get_quote line 87-90）：
        if quote == None and is_trade:
            'trade'      # (实际产物为三引号 docstring 形式)
        else:
            'backtest'
    —— 原始 `quote = Quote(log, 'trade' if is_trade else 'backtest')` 中，
       函数实参位置的 IfExp（`'trade' if is_trade else 'backtest'`）被误读为
       `if` 语句的 `and` 条件（`and is_trade`），Quote 调用整体丢失，
       IfExp 两支的字符串常量 ('trade'/'backtest') 被作为孤立 docstring 语句
       留在 if/else 体内。

触发区域类型：IF + BOOLOP(and) + TERNARY(IfExp 作函数实参)
根因初判：
    `core/cfg/region_ast_generator.py::_generate_if` 把
    `LOAD_FAST is_trade; POP_JUMP_IF_FALSE; LOAD_CONST 'trade'; JUMP; LOAD_CONST 'backtest'`
    （IfExp 作为 Quote() 第二实参的求值序列）误归约为 if 语句的条件 `and is_trade`，
    而把 IfExp 两支的字符串常量误发射为 docstring 语句体。
    违反「入口引用语义」+「嵌套即抽象节点」：IfExp 应作为 Call 实参子节点。

最小字节码模式（Python 3.11，IfExp 作函数实参）：
    LOAD_GLOBAL quote
    POP_JUMP_FORWARD_IF_NOT_NONE to <end>      # if quote is None:
    LOAD_GLOBAL getLogger / CALL / UNPACK_SEQUENCE 2  # log, is_trade = getLogger()
    LOAD_GLOBAL Quote                          # callable
    LOAD_FAST log                              # arg1
    LOAD_FAST is_trade                         # arg2 = IfExp condition
    POP_JUMP_IF_FALSE to <else_branch>
    LOAD_CONST 'trade'
    JUMP_FORWARD to <merge>
  <else_branch>:
    LOAD_CONST 'backtest'
  <merge>:
    PRECALL 2 / CALL 2                         # Quote(log, <ifexp>)
    STORE_GLOBAL quote
  <end>:
    LOAD_GLOBAL quote / RETURN_VALUE

R2 反编译产物（错误）：
    if quote == None and is_trade:
        'trade'      # (实际为三引号 docstring 形式)
    else:
        'backtest'
期望产物：
    if quote is None:
        log, is_trade = getLogger()
        quote = Quote(log, 'trade' if is_trade else 'backtest')
    return quote

验证：python pycdc.py <this>.pyc  # 观察 IfExp 实参 → and + docstring 体
"""
def get_quote():
    global quote
    if quote is None:
        log, is_trade = getLogger()
        quote = Quote(log, 'trade' if is_trade else 'backtest')
    return quote
