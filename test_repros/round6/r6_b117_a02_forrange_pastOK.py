# Source Generated with Decompyle++ (Python version)
# File: r6_b117_a02_forrange_past.pyc (Python 3.11)

def r6_b117_a02_forrange_past(n):
    acc = 0
    for i in range(n):
        acc += i
    step = n * 2 + 1
    pad = step - n
    for j in range(step + pad):
        acc += j
    return acc
