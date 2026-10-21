# Source Generated with Decompyle++ (Python version)
# File: l0_a4_triple_while_try_for.pyc (Python 3.11)

__doc__ = 'AT-02: while x try x for —— 三元嵌套，for-else + try-else 混合'
def a4(xs):
    try:
        for x in xs:
            if x:
                break
            continue
    except Exception:
        return None
