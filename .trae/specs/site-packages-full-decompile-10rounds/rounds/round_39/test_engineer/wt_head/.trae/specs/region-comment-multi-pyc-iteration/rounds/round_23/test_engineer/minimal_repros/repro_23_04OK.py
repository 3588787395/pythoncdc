# Source Generated with Decompyle++ (Python version)
# File: repro_23_04.cpython-311.pyc (Python 3.11)

def while_continue_post(data, n):
    j = 0
    result = []
    while j < n:
        if data[j] < 0:
            j += 1
            continue
        result.append(data[j])
        j += 1
    count = len(result)
    return count
