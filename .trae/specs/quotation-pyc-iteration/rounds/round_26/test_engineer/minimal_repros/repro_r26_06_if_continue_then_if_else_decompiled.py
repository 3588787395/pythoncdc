# Source Generated with Decompyle++ (Python version)
# File: repro_r26_06_if_continue_then_if_else.pyc (Python 3.11)

def f(items, out):
    for k, v in items.items():
        if k == 'skip':
            continue
        elif k == 'a':
            out.append(v)
            continue
        else:
            out[k] = v
            continue
