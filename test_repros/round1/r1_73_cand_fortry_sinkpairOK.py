# Source Generated with Decompyle++ (Python version)
# File: r1_73_cand_fortry_sinkpair.pyc (Python 3.11)

def f73(r, v):
    if v == 3:
        for _ in r:
            try:
                print('get')
            except ValueError:
                print('empty')
            print('ok')
        return None
    elif v == 5:
        print('five')
    return None
