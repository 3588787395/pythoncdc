"""repro_01 — 缺陷1: IF then 分支吸收循环末尾的兄弟 if 语句。

模式（取自 change_his_to_backward）：
  for 循环体内 if/elif/else 链，then 与 elif/else 各分支均 JUMP_FORWARD 到
  循环末尾的兄弟 if 块（每轮无条件执行，break 除外）。
  反编译器把循环末尾的兄弟 if 错误并入 then 分支，导致 POP_JUMP_FORWARD_IF_NOT_NONE
  跳转目标变大，elif/else 分支丢失兄弟 if。

期望字节码：then 分支末尾 JUMP_FORWARD → 兄弟 if 入口（非 JUMP_BACKWARD 直接到循环头）。
"""
def f(items):
    pre = None
    out = []
    for n in items:
        if pre is None:
            out.append(n)
        elif n == 0:
            break
        else:
            out.append(n + 1)
        if pre != n:
            pre = n
        if len(out) != 0:
            pass
    return out
