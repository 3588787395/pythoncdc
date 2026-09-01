# Source Generated with Decompyle++ (Python version)
# File: repro_23_09.pyc (Python 3.11)

def walrus_while(n):
    j = (i := 0)
    while j < n:
        i = j
        j += 1
    return i
