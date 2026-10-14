# Source Generated with Decompyle++ (Python version)
# File: r1_70_cand_chain_controls.pyc (Python 3.11)

K = {}
def f70(t):
    if t == 'a':
        print('A')
    elif t in K:
        print('B')
    else:
        print('C')
    print('after')
def f71(t):
    if t == 'a':
        print('A')
        return None
    elif t in K:
        print('B')
        return None
    else:
        print('C')
