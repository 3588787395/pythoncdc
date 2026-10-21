# Source Generated with Decompyle++ (Python version)
# File: l3_o5_overlay_augassign_del_slice.pyc (Python 3.11)

__doc__ = """L3 §4 叠加攻击 (e) — augassign + delete + slice + return 同处一个表达式/语句上下文。

关注：B145（del 归约 ast.Delete + break 落点）、B148（复合前缀算子族含
     BINARY_SUBSCR / BUILD_SLICE）、B149（尾随 SWAP/POP_TOP 剥离）、
     B150（双臂 return 折叠）在同一函数内的优先级。
"""
def o5(d, xs, k):
    total = 0
    for x in xs:
        d[x] += k
        total += x if x else 0
    del d[::2]
    return total
def o5b(d, xs, k):
    """del 的 slice 边界含 augassign 的结果（三元 + 变量）。"""
    total = 0
    for x in xs:
        n = x + k
        d[x] += k
        total += n if n else 0
    return total
