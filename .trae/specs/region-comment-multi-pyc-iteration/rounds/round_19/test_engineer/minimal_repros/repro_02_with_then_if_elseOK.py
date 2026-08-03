# Source Generated with Decompyle++ (Python version)
# File: repro_02_with_then_if_else.pyc (Python 3.11)

def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if b is not None:
        x = 'a_' + b
    else:
        x = 'default'
    return x
