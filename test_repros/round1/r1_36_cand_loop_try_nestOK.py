# Source Generated with Decompyle++ (Python version)
# File: r1_36_cand_loop_try_nest.pyc (Python 3.11)

def f36(xs):
    try:
        for x in xs:
            if x == 1:
                if x == 2:
                    print('a')
                else:
                    print('b')
                print('c')
                continue
            print('d')
    except BaseException as exc:
        print(exc)
        return None
