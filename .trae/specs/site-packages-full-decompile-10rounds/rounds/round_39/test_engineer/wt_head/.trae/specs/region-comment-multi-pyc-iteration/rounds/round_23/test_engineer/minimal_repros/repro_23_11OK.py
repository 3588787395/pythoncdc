# Source Generated with Decompyle++ (Python version)
# File: repro_23_11.cpython-311.pyc (Python 3.11)

def for_continue(items):
    result = []
    for item in items:
        if item < 0:
            continue
        result.append(item)
    return result
