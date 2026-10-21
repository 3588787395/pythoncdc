# Source Generated with Decompyle++ (Python version)
# File: l0_c5_continue_in_nested_try_finally.pyc (Python 3.11)

__doc__ = 'AT-01/AT-04: try/finally 内 continue，finally 副本与 continue 目标双重归属'
def c5(xs):
    for a in xs:
        try:
            if a:
                continue
            print('fin')
            continue
        finally:
            print('fin')
