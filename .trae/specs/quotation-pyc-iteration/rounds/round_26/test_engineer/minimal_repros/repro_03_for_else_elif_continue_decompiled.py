# Source Generated with Decompyle++ (Python version)
# File: repro_03_for_else_elif_continue.pyc (Python 3.11)

def f(items, out):
    for k, v in items.items():
        if k == 'a':
            continue
        elif isinstance(v, dict):
            out.update(v)
            continue
        else:
            out[k] = v
            continue
    out.append(0)
