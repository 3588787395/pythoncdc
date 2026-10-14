# Source Generated with Decompyle++ (Python version)
# File: r1_34_cand_module_try_nest.pyc (Python 3.11)

try:
    if __name__ == 'x':
        print('a')
        if __name__ == 'y':
            print('b')
        else:
            print('c')
        print('d')
    else:
        print('e')
except BaseException as exc:
    print(exc)
