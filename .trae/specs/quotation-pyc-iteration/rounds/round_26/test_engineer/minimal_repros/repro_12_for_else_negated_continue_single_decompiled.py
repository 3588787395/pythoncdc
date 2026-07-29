# Source Generated with Decompyle++ (Python version)
# File: repro_12_for_else_negated_continue_single.pyc (Python 3.11)

def f(items, out):
    for k, v in items.items():
        if not k == 'skip':
            out[k] = v
            continue
        continue
    out.append(0)
