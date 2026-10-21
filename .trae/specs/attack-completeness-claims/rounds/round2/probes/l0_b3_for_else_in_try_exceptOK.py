# Source Generated with Decompyle++ (Python version)
# File: l0_b3_for_else_in_try_except.pyc (Python 3.11)

__doc__ = 'AT-04: for-else 位于 try/except 体内（无 finally）'
def b3(xs):
    try:
        for x in xs:
            print(x)
        print('else')
        return None
    except Exception:
        return None
