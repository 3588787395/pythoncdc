# Source Generated with Decompyle++ (Python version)
# File: l0_a1_triple_if_for_try.pyc (Python 3.11)

__doc__ = 'AT-02: if x for x try —— 三元嵌套，try 体含 continue/break'
def a1(xs):
    if xs:
        for x in xs:
            try:
                if x:
                    continue
                else:
                    break
            except ValueError:
                pass
        else:
            print('for-else')
    return 0
