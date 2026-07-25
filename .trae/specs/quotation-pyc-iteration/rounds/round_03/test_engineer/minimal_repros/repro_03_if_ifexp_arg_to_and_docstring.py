"""
Defect R3-06 (R1/R2 残留) — IF/BOOLOP + IfExp：函数实参位置 IfExp 被误读为 `and`，赋值体塌缩为 docstring
================================================================
关联 R1/R2 repro：repro_06_if_boolop_and_decompose / repro_06_if_ifexp_arg_to_and_docstring

R3 复现状态：**R2 未修复，quotation.pyc::get_quote (line 87-90) 仍复现**。
  R3 表现（quotation.pyc::get_quote）：
        if quote is None and is_trade:
            'trade'                     # ← IfExp 一支常量被误发射为 docstring (三引号)
        else:
            'backtest'                  # ← IfExp 另一支常量被误发射为 docstring (三引号)
        return quote
  Quote(log, 'trade' if is_trade else 'backtest') 调用整体丢失。

触发区域类型：IF + BOOLOP(and) + TERNARY(IfExp 作函数实参)
根因初判：
    `region_ast_generator.py::_generate_if` 把
    `LOAD_FAST is_trade; POP_JUMP_IF_FALSE; LOAD_CONST 'trade'; JUMP; LOAD_CONST 'backtest'`
    （IfExp 作为 Quote() 第二实参的求值序列）误归约为 if 条件 `and is_trade`，
    IfExp 两支字符串常量被误发射为 docstring 语句体，Quote 调用整体丢失。
    违反「入口引用语义」+「嵌套即抽象节点」。

最小字节码模式（Python 3.11）：
    LOAD_FAST quote
    POP_JUMP_IF_NOT_NONE              # if quote is None:
    LOAD_FAST is_trade                #   ← IfExp 条件
    POP_JUMP_IF_FALSE                 #   ← 被误并入 if 条件 (and is_trade)
    LOAD_CONST 'trade'                #   ← IfExp 真支  ← 误作 docstring
    JUMP
    LOAD_CONST 'backtest'             #   ← IfExp 假支  ← 误作 docstring
    LOAD_GLOBAL Quote
    LOAD_FAST log
    ...
    CALL                              # ← Quote(log, IfExp) 调用整体丢失

R3 反编译产物（错误）：
    global quote
    quote = None
    def get_quote():
        global quote
        log = getLogger()
        if quote is None and is_trade:
            'trade'                  # 实际为三引号 docstring
        else:
            'backtest'               # 实际为三引号 docstring
        return quote

期望产物：
    def get_quote():
        global quote
        log, is_trade = getLogger()
        if quote is None:
            quote = Quote(log, 'trade' if is_trade else 'backtest')
        return quote

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_if_ifexp_arg_to_and_docstring.py', 'repro_03_if_ifexp_arg_to_and_docstring.pyc', doraise=True)"
    $ python pycdc.py repro_03_if_ifexp_arg_to_and_docstring.pyc
    # 观察 IfExp 两支字符串被发射为 docstring，Quote 调用丢失
"""
quote = None
def get_quote():
    global quote
    log, is_trade = getLogger()
    if quote is None:
        quote = Quote(log, 'trade' if is_trade else 'backtest')
    return quote
