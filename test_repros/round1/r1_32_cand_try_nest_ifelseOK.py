# Source Generated with Decompyle++ (Python version)
# File: r1_32_cand_try_nest_ifelse.pyc (Python 3.11)

def f32(x):
    try:
        if x == 1:
            if x == 2:
                print('a')
            else:
                print('b')
            print('c')
            return None
        else:
            print('d')
            return None
    except BaseException as exc:
        print(exc)
        return None
