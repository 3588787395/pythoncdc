# Source Generated with Decompyle++ (Python version)
# File: o1.pyc (Python 3.11)

def f(sig, pred):
    if not (sig == 'a' or sig == 'b'):
        if (sig == 'c' or sig == 'd') and not pred.isdigit():
            tag = pred[0]
            return tag
        if sig == 'e':
            return 'E'
        else:
            raise ValueError('bad')
