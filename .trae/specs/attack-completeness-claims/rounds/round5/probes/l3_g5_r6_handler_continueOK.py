# Source Generated with Decompyle++ (Python version)
# File: l3_g5_r6_handler_continue.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检 — 族 R6（循环控制族）。

新构型（非语料）：
  `except` handler 内的 **continue**（B140 只登记 handler 内的 **break**；
  B106/B145 只处理 break 落点 / 回边）。handler 内的 continue 在 CPython 3.11
  被编译为 POP_EXCEPT + JUMP_BACKWARD(循环头)。
判据问题：B140 的「handler break 识别」五合取判据
  （region_analyzer.py:36342-36357）是否可迁移到同族的 handler **continue**？
  若其触发谓词绑定「无条件前向跳转 + 目标是循环出口块」，则 continue
  （回向循环头）必然不命中 ⇒ continue 语句丢失 ⇒ 语义差。
"""
def r6_handler_continue(xs):
    out = []
    for x in xs:
        try:
            if x < 0:
                raise ValueError(x)
        except ValueError:
            continue
        out.append(x)
    return out
def r6_handler_continue_while(xs):
    out = []
    i = 0
    while i < len(xs):
        try:
            if xs[i] < 0:
                raise ValueError(xs[i])
        except ValueError:
            i += 1
        out.append(xs[i])
        i += 1
    return out
