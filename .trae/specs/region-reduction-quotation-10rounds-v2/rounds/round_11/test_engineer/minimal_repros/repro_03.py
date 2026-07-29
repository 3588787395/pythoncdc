"""repro_03: load_get_price BoolOp `x in (tuple)` 条件入口跳转目标归一化 (-1 残留)
区域类型: BoolOp + Conditional
违反原则: 4 (入口引用语义)
对应函数: load_get_price
缺陷镜像: `if _typet in (7,8,9,15):` 的 POP_JUMP_FORWARD_IF_FALSE 目标在 new 中归一化为 -1
  (目标 offset 不在过滤后指令表内)，CONTAINS_OP 后跳转目标指向条件 then 入口的语义未对齐。
  diff_detail idx 168: orig POP_JUMP_FORWARD_IF_FALSE ->[198] vs new ->[-1]。
"""


def f(panel, _typet, stocks):
    if _typet in (7, 8, 9, 15):
        panel = get_str(panel, _typet)
    if isinstance(stocks, str):
        rdata = panel
    else:
        rdata = panel[stocks]
    return rdata


def get_str(panel, _typet):
    return panel
