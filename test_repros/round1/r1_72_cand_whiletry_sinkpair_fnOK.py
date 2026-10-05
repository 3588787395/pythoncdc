# Source Generated with Decompyle++ (Python version)
# File: r1_72_cand_whiletry_sinkpair_fn.pyc (Python 3.11)

def f72(r):
    while r:
        try:
            print('get')
        except ValueError:
            print('empty')
        else:
            print('ok')
    return None
