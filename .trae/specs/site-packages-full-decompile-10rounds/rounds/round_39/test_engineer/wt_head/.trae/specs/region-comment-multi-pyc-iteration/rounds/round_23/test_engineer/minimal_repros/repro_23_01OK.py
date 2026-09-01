# Source Generated with Decompyle++ (Python version)
# File: repro_23_01.pyc (Python 3.11)

def while_post_if(n):
    j = 0
    i = 0
    while j < n:
        if j % 2 == 0:
            i = j
        j += 1
    if j == n:
        return i
    else:
        return -1
