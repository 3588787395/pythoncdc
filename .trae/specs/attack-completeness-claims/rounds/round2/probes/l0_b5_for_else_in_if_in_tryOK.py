# Source Generated with Decompyle++ (Python version)
# File: l0_b5_for_else_in_if_in_try.pyc (Python 3.11)

__doc__ = 'AT-04: for-else 位于 try 体内的 if 分支中'
def b5(xs):
    try:
        if xs:
            for x in xs:
                print(x)
            print('else')
        return None
    except Exception:
        return None
