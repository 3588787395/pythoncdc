# Source Generated with Decompyle++ (Python version)
# File: o1.pyc (Python 3.11)

def f(sig, pred):
    if sig == 'a' or sig == 'b' or (sig == 'c' or sig == 'd') and not pred.isdigit():
        tag = pred[0]
        return tag
    elif sig == 'e':
        return 'E'
    else:
        raise ValueError('bad')
