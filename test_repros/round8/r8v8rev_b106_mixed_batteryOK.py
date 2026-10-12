# Source Generated with Decompyle++ (Python version)
# File: r8v8rev_b106_mixed_battery.pyc (Python 3.11)

def v1(f, a, b, kw):
    return f(a, *b, **(kw))
def v2(f, a, b):
    return f(*a, *b)
def v3(k, a):
    g = lambda *a, **k: k(*a)
    return g(*a, m=1)
def v4(f, xs, d):
    return [f(*xs, v) for v in d]
