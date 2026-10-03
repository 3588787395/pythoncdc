"""rv6_03: bare-None 尾声两形态同函数共存（B34b 细化判据双向）。

同一函数内并存：
  - 形态 A：exit-block 由条件前驱 POP_JUMP_* 假边直达（if-else 假分支尾声
    与函数尾隐式 return 同位 → 应收编走隐式过滤）；
  - 形态 B：exit-block 仅由无条件边（fall-through/JUMP_FORWARD）到达
    （外层 with 的 exit-block → 应拒收、交 F5 顶层显式发射）。
"""


def cond_edge_tail(v, m1):
    with m1:
        if v:
            x = 1
        else:
            x = 2
    return None


def uncond_edge_tail(xs, m2):
    with m2:
        xs.append(1)
    return xs


def dual_form_coexist(v, m1, m2, xs):
    out = 0
    with m1:
        if v:
            out += 1
        else:
            out -= 1
    with m2:
        out *= 2
    return out
