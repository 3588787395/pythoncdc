# Source Generated with Decompyle++ (Python version)
# File: l0_c4_finally_copy_continue.pyc (Python 3.11)

__doc__ = 'AT-01/AT-04: finally 副本 + continue —— 副本归属与 continue 目标同时命中'
def c4(xs):
    for a in xs:
        try:
            print('fin')
        finally:
            print('fin')
