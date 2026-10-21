# Source Generated with Decompyle++ (Python version)
# File: l0_e7_proj_try_for_else.pyc (Python 3.11)

__doc__ = 'AT-04 二元投影: try x for-else（b5 的 try+for-else 子投影）'
def e7(xs):
    try:
        for x in xs:
            print(x)
        print('else')
        return None
    except Exception:
        return None
