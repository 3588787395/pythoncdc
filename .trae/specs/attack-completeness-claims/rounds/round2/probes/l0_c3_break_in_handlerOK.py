# Source Generated with Decompyle++ (Python version)
# File: l0_c3_break_in_handler.pyc (Python 3.11)

__doc__ = 'AT-04: handler 体内 break（B140 形态），break 落点在循环之外'
def c3(xs):
    for a in xs:
        try:
            print(a)
        except Exception:
            break
    return 0
