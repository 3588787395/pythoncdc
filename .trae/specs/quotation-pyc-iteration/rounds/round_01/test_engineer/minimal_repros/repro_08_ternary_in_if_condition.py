"""
Defect 08 — TERNARY/IF: `if (ternary):` 条件被替换为 `len(ternary)` 裸表达式
================================================================
触发区域类型：TERNARY (IfExp) + IF
根因初判：
    core/cfg/region_ast_generator.py `_generate_if` /
    `_generate_ifexp` 在处理 `if (A if B else (C if D else E)):` 这种
    条件位置为嵌套三元表达式的情况时，把 if 语句的 condition
    错误归约为一个孤立的 Expr 语句，且在最外层套上了 `len(...)`
    （来自 COPY 1 + LOAD_GLOBAL len 的栈对齐误读）。原始 `if`
    关键字丢失，三元表达式被包裹成 `len(...)` 作为表达式语句。
    违反「父引用子入口」：IfExp 应作为 If.condition 的子节点，
    不应被单独提升为语句。

最小字节码模式（Python 3.11，嵌套 IfExp 作 if 条件）：
    <A>
    COPY 1
    <B>
    POP_JUMP_IF_FALSE to <else1>
    <A-true>
    JUMP_FORWARD to <end1>
  <else1>:
    <C>
    COPY 1
    <D>
    POP_JUMP_IF_FALSE to <else2>
    <C-true>
    JUMP_FORWARD to <end2>
  <else2>:
    <E>
  <end2>/<end1>:
    POP_JUMP_IF_FALSE to <after-if>     # ← 这一层 if 被丢失
    <if-body>
  <after-if>:

反编译产物（错误）：
    len(len(start[8:]) == 4 if len(data) > 0 else is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty)
期望产物：
    if len(start[8:]) == 4 if len(data) > 0 else (is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty):
        pass

验证：python pycdc.py <this>.pyc  # 观察 if 被替换为 len(...) 裸表达式
"""
def load_get_price(stocks, typet, start, end, count, fq=None):
    panel = load_bars(stocks, typet, start, end)
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    if len(start[8:]) == 4 if len(data) > 0 else is_utc == '0' if len(panel.major_axis) != 0 else retpanel.empty:
        pass
    return rdata
