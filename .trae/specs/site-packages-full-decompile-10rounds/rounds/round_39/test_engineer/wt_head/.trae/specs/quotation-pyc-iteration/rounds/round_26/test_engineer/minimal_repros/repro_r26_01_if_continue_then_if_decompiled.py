# Source Generated with Decompyle++ (Python version)
# File: repro_r26_01_if_continue_then_if.pyc (Python 3.11)

def f(items, out):
    for key, value in items.items():
        if key == 'skip':
            continue
        elif key == 'a':
            continue
        elif isinstance(value, dict):
            out.update(value)
            continue
        else:
            out[key] = value
            continue
    out.append(0)
