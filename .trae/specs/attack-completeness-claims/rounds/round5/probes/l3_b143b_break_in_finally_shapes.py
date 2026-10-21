"""L3 §5 — B143（finally 体内 break 的 finalbody 子区域派发）形态枚举。

原始复现（B143 登记原文，attain-true-completeness/rounds/round6/FIX.md:93）：
  `s_b140_break_in_finally_loop`（仓内原件：test_repros/round6/r6_synth_b140_nested_break.py:15）
  根因自述：「finally 体（副本序列）中的嵌套 IfRegion 条件块与 break 臂块在
  finalbody 装配时线性发射，break 未落在 if 臂内（`if i == 1: pass` + 臂外 break/continue）」。

本探针枚举 finally 体内 break 的**宿主/位置**维度：
  A  for 体 + finally + if 臂内 break                （单层循环）
  B  for > while > try/finally + if 臂内 break       （B143 原件逐字复刻）
  C  for > while > try/finally + **臂外**（finally 级）break
  D  for 体 + finally + if/else 双臂（break / continue）
  E  for > while > try/finally + while-else
源语义要点：finally 体内的 break 必须（i）留在 finally 体内、
  （ii）落在正确的 if 臂内、（iii）跳出**所属循环**（内层 while，不是外层 for）。
"""


def b143_a_for_finally_ifarm(n):
    out = []
    for i in range(n):
        try:
            out.append(i)
        finally:
            if i == 1:
                break
    return out


def b143_b_orig_nested(n):
    """B143 原件逐字复刻：break 属于内层 while。"""
    out = []
    for i in range(n):
        while i > 0:
            i -= 1
            try:
                out.append(i)
            finally:
                if i == 1:
                    break
    return out


def b143_c_break_outside_arm(n):
    """臂外 break：finally 体里 if 之后再 break（不在任何 if 臂内）。"""
    out = []
    for i in range(n):
        while i > 0:
            i -= 1
            try:
                out.append(i)
            finally:
                if i == 1:
                    out.append(-1)
                break
    return out


def b143_d_if_else_arms(n):
    """if/else 双臂：break 在 if 臂、continue 在 else 臂。"""
    out = []
    for i in range(n):
        while i > 0:
            i -= 1
            try:
                out.append(i)
            finally:
                if i == 1:
                    break
                else:
                    continue
    return out


def b143_e_while_else(n):
    """while-else + finally 内 break。"""
    out = []
    for i in range(n):
        while i > 0:
            i -= 1
            try:
                out.append(i)
            finally:
                if i == 1:
                    break
        else:
            out.append("inner-done")
    return out
