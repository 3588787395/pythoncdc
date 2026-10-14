# Source Generated with Decompyle++ (Python version)
# File: r1_94_regress_b98win_try_ifelse_hret.pyc (Python 3.11)

def f94(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
    except BaseException:
        print('e')
        return None
    return None
