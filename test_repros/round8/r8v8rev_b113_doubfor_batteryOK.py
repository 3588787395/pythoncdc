# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_b113_doubfor_battery.pyc (Python 3.11)

def v1(a, b):
    return [i * j for i in a for j in b if i > j]
def v2(m):
    return [[k for k in row] for row in m]
def v3(a, b, k):
    return [(i, j, w) for i in a for j in b if i > j for w in k if w > i]
def v4(xs):
    return {i: j for i in xs for j in xs if i < j}
