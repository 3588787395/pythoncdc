# Source Generated with Decompyle++ (Python version)
# File: rv6_07_foreach_fused_return.pyc (Python 3.11)

__doc__ = """rv6_07: for-else 融合 return 认领（B36-f 变体）——while-else 宿主 + 多语句 else + 双层循环 else。

对照 r6_10.w_break_in_with（for-else 内 return 融合 with-exit 单块）：
换循环宿主（while-else）与 else 体形态（多语句 / 无 return 的纯透传），
检验 else 链穿透认领判据在宿主结构改变下不误吞、不漏认。
"""
def while_else_fused_return(mgr, xs):
    with mgr:
        while xs:
            x = xs.pop()
            if x:
                break
        else:
            while False:
                pass
            return -1
    return 0
def for_else_multi_stmt(mgr, xs):
    out = 5
    with mgr:
        for x in xs:
            if x < 0:
                break
        else:
            out += 1
            return out
    return out
def nested_loop_else(mgr, xs, ys):
    for x in xs:
        for y in ys:
            if y == x:
                break
        else:
            return x
