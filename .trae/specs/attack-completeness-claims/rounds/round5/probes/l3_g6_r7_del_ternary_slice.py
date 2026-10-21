"""L3 §3 通用性抽检 — 族 R7（赋值 / 删除 / return / slice 族）。

新构型（非语料）：
  `del` 的 **slice 边界是三元表达式**（含 step），且在循环体内；
  已落地的 B148 把「值折叠算子族」纳入「复合前缀」判据（BINARY_OP /
  BUILD_SLICE / BINARY_SUBSCR / COMPARE_OP / ...），B145 处理 break 落点与
  del 归约 ast.Delete。
判据问题：B148 的「复合前缀」判据是否覆盖「三元作为 slice 边界」这一
  位置（而非「三元作为条件表达式」）？del + slice + 循环体三者叠加时
  是否仍归约为 ast.Delete？
"""


def r7_del_ternary_slice(d, xs):
    for x in xs:
        del d[x if x else 0::2]
    return d


def r7_augassign_ternary_slice(d, xs, k):
    for x in xs:
        d[x if x else 0::2] += k
    return d
