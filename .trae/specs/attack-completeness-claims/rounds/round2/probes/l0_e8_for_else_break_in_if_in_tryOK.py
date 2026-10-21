# Source Generated with Decompyle++ (Python version)
# File: l0_e8_for_else_break_in_if_in_try.pyc (Python 3.11)

__doc__ = 'AT-04 语义强化: for-else 体含 break 时，else 归属错误即产生**可观测语义差**'
def e8(xs):
    try:
        if xs:
            for x in xs:
                if x:
                    pass
                print(x)
            print('else')
        return None
    except Exception:
        return None
