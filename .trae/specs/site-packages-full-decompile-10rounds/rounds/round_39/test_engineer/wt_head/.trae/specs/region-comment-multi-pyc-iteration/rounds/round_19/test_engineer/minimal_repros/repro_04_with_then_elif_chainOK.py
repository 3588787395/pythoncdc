# Source Generated with Decompyle++ (Python version)
# File: repro_04_with_then_elif_chain.pyc (Python 3.11)

def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if b == 1:
        x = 'one'
    elif b == 2:
        x = 'two'
    else:
        x = 'other'
    return x
