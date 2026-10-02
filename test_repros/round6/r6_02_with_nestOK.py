# Source Generated with Decompyle++ (Python version)
# File: r6_02_with_nest.pyc (Python 3.11)

def w_nest3(m1, m2, m3):
    with m1, m2, m3:
        return 3
def w_nest_same_name(m1, m2):
    with m1 as x, m2 as x:
        return x
def w_with_if(mgr, v):
    with mgr as x:
        if v:
            x
def w_with_for(mgr, xs):
    with mgr:
        total = 0
        for x in xs:
            total += x
        return total
def w_with_while(mgr, n):
    with mgr:
        i = 0
        while i < n:
            i += 1
        return i
def w_with_try(mgr, xs):
    with mgr:
        try:
            return len(xs)
        except TypeError:
            return 0
