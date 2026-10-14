# Source Generated with Decompyle++ (Python version)
# File: r1_60_cand_tryret_hret.pyc (Python 3.11)

def f60(x):
    try:
        if x:
            print('a')
        return x
    except BaseException:
        print('e')
        return x
