# Source Generated with Decompyle++ (Python version)
# File: r1_95_regress_if_for_tail_in_try.pyc (Python 3.11)

def f95(x, items, store):
    try:
        if x:
            for k in items:
                store.pop(k)
    except BaseException:
        print('e')
        return None
    return None
