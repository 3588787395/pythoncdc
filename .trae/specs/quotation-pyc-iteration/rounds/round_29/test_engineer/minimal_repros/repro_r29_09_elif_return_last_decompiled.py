# Source Generated with Decompyle++ (Python version)
# File: repro_r29_09_elif_return_last.pyc (Python 3.11)

def f(x, d):
    if x == 1:
        d = d[1]
        result = []
        for k in d:
            result.append(k)
        return result
    elif x == 2:
        d = d[2]
    elif x in d:
        return d[x]
