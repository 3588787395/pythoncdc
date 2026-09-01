# Source Generated with Decompyle++ (Python version)
# File: repro_23_05.cpython-311.pyc (Python 3.11)

def for_after_if_return(items, check):
    if len(items) == 0:
        return items
    else:
        result = []
        for item in items:
            if item == check:
                result.append(item)
            continue
        return result
