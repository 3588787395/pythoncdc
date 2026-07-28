# Source Generated with Decompyle++ (Python version)
# File: repro_r26_03_if_continue_then_elif.pyc (Python 3.11)

def f(items, out):
    for k, v in items.items():
        if k == 'skip':
            continue
        elif k == 'x':
            continue
        elif isinstance(v, dict):
            out.update(v)
            continue
        else:
            out[k] = v
            continue
