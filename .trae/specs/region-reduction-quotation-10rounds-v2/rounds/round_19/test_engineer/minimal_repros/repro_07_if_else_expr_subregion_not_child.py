"""repro_07: IfRegion else 分支含表达式子区域但不在 children 中。

_process_if_blocks 仅遍历 region.children 收集 BoolOpRegion/TernaryRegion。
当三元的 parent 是外层 LoopRegion（非 IfRegion），三元不出现在 IfRegion.children，
但其 entry 落在 IfRegion.else_blocks 中，导致遗漏。
"""


def f(data, n):
    out = {}
    for i in range(n):
        if i < 0:
            continue
        else:
            out[i] = i if i > 5 else -i
    return out
