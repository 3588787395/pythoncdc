# Source Generated with Decompyle++ (Python version)
# File: repro_11_ctrl_with_in_if.pyc (Python 3.11)

def f(p, b):
    if b is not None:
        with open(p, 'r', encoding='utf-8') as fh:
            content = fh.read()
        x = content + '_' + b
    else:
        x = 'default'
    return x
