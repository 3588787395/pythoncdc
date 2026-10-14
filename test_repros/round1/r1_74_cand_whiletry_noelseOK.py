# Source Generated with Decompyle++ (Python version)
# File: r1_74_cand_whiletry_noelse.pyc (Python 3.11)

def f74(r, v):
    if v == 3:
        while r:
            try:
                print('get')
            except ValueError:
                print('empty')
        return None
    elif v == 5:
        print('five')
    return None
