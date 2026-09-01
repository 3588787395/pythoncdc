# Source Generated with Decompyle++ (Python version)
# File: repro_23_02.pyc (Python 3.11)

def while_then_for(data, n):
    j = 0
    i = 0
    indexes = []
    while j < n:
        if data[j] > 0:
            indexes.append(i)
            i = j
        j += 1
    if j == n:
        indexes.append(i)
    result = []
    for idx in indexes:
        result.append(data[idx])
    return result
