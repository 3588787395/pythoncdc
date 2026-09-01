# Source Generated with Decompyle++ (Python version)
# File: repro_20_for_else_simple.pyc (Python 3.11)

def func(items):
    result = {}
    for item in items:
        val = int(item)
        if val > 0:
            result[item] = val
        continue
    else:
        if result:
            return result
        else:
            raise ValueError('empty')
