# Source Generated with Decompyle++ (Python version)
# File: l3_g5b_r6_handler_continue_matrix.pyc (Python 3.11)

__doc__ = """L3 §3 通用性抽检（判别矩阵）— 族 R6：handler 内 continue 的失败因子判别。

R6 落地声明（attain-true-completeness/rounds/round6/FIX.md:90）称
「通用性实证：6 个非语料合成探针 22/23 覆盖 … handler break/continue（while + for）」。
但仓内实际探针只有：
  test_repros/round6/r6_synth_b140_handler_break.py:1  `s_b140_handler_break`      = while + handler break
  test_repros/round6/r6_synth_b140_handler_break.py:22 `s_b140_handler_continue`   = for  + handler continue
  ⇒ 「while × continue」这一格**未被覆盖**。

本探针给出 2×2 判别矩阵（循环宿主 {for, while} × continue 前是否有语句），
用于判别 §3 探针 `l3_g5_r6_handler_continue` 中 `r6_handler_continue_while` 失败的
根因是「宿主是 while」还是「continue 前有语句」。
"""
def r6_for_bare_continue(xs):
    out = []
    for x in xs:
        try:
            if x < 0:
                raise ValueError(x)
        except ValueError:
            continue
        out.append(x)
    return out
def r6_for_stmt_continue(xs):
    out = []
    for x in xs:
        try:
            if x < 0:
                raise ValueError(x)
        except ValueError:
            out.append(-1)
            continue
        out.append(x)
    return out
def r6_while_bare_continue(xs):
    out = []
    i = 0
    while i < len(xs):
        try:
            if xs[i] < 0:
                raise ValueError(xs[i])
        except ValueError:
            continue
        out.append(xs[i])
        i += 1
    return out
def r6_while_stmt_continue(xs):
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
