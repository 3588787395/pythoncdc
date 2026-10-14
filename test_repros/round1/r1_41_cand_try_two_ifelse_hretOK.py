# Source Generated with Decompyle++ (Python version)
# File: r1_41_cand_try_two_ifelse_hret.pyc (Python 3.11)

def f41(x):
    try:
        if x == 1:
            print('a')
        else:
            print('b')
        if x == 2:
            print('c')
            return None
        else:
            print('d')
            return None
    except BaseException:
        print('e')
        return None
