# Source Generated with Decompyle++ (Python version)
# File: repro_01_for_else_after_continue_chain.pyc (Python 3.11)

def f(items, result):
    for key, value in items.items():
        if not key == 'skip':
            if key == 'a':
                continue
            result.append(value)
        else:
            continue
    result.append(-1)
