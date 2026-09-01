"""
Defect 06 — IF/BOOLOP: `if A and B:` 被错误分解为嵌套 `if A: if B:`，else 语义改变
================================================================
触发区域类型：IF + BOOLOP (and)
根因初判：
    core/cfg/region_analyzer.py `_identify_if_regions` 在归约
    `if A and B: X else: Y` 时，把 `and` 短路跳转的两段条件块
    错误识别为两个嵌套的 IfRegion（外层 `if A:`，内层 `if B:`），
    而把 `else: Y` 归到外层 if。但原始 `else` 语义是
    `not (A and B) = not A or not B`，重建后变成 `not A`，
    丢失了 `not A and B` 与 `A and not B` 两种情况。
    违反「父引用子入口」：BoolOp(and) 应作为 If.condition 的单一
    子节点，不应拆成两层 If。

最小字节码模式（Python 3.11，`if A and B:` with else）：
    LOAD_GLOBAL quote
    POP_JUMP_FORWARD_IF_NOT_NONE to <else>     # A: quote is None
    LOAD_GLOBAL is_trade
    POP_JUMP_FORWARD_IF_FALSE to <else>        # B: is_trade
    <if-body: quote = Quote(log, is_trade)>
    JUMP_FORWARD to <end>
  <else>:
    <else-body: quote = Quote()>
  <end>:

反编译产物（错误，else 语义改变）：
    if quote is None:
        if is_trade:
            quote = Quote(log, is_trade)
    else:
        quote = Quote()
    return quote
期望产物：
    if quote is None and is_trade:
        quote = Quote(log, is_trade)
    else:
        quote = Quote()
    return quote

验证：python pycdc.py <this>.pyc  # 观察 and 被拆为嵌套 if
"""
def get_quote():
    global quote
    log, is_trade = getLogger()
    if quote is None and is_trade:
        quote = Quote(log, is_trade)
    else:
        quote = Quote()
    return quote
