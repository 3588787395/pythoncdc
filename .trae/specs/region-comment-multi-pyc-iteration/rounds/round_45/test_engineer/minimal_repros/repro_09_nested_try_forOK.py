# Source Generated with Decompyle++ (Python version)
# File: repro_09_nested_try_for.pyc (Python 3.11)

def func(items):
    result = []
    for item in items:
        try:
            result.append(item * 2)
        except TypeError:
            result.append(0)
            continue
    else:
        return result
