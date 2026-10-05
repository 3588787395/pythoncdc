# Source Generated with Decompyle++ (Python version)
# File: r1_33_cand_try_ifelse_then_stmt.pyc (Python 3.11)

def f33(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
        print('after')
        return None
    except BaseException as exc:
        print(exc)
        return None
