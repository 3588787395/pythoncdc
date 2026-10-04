# Source Generated with Decompyle++ (Python version)
# File: r10_12_global_deep.pyc (Python 3.11)

global STATE
__doc__ = 'r10_12: global 三层嵌套函数（closure 链最内层声明，深度 ≥3）'
STATE = []
def g_level3(seed):
    def mid(n):
        def inner(k):
            nonlocal_local = k
            if k > 0:
                STATE.append((seed, n, k))
            return STATE
        return inner(n)
    return mid(seed)
def g_two_globals(a, b):
    def outer(p):
        def inner(q):
            global STATE
            if q % 2:
                STATE = [p, q]
            return STATE
        return inner(p)
    return outer(a) if b else None
