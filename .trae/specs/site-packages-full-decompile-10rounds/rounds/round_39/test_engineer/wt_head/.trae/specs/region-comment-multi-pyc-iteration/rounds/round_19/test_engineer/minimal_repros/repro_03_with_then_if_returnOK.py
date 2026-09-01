# Source Generated with Decompyle++ (Python version)
# File: repro_03_with_then_if_return.pyc (Python 3.11)

def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if b is None:
        return 'none'
    else:
        return b + '_tail'
