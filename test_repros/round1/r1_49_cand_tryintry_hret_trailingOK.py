# Source Generated with Decompyle++ (Python version)
# File: r1_49_cand_tryintry_hret_trailing.pyc (Python 3.11)

def f49(x):
    try:
        try:
            if x == 1:
                print('a')
            else:
                print('b')
        except ValueError:
            print('inner')
    except BaseException:
        print('e')
        return None
    return None
