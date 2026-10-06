# Source Generated with Decompyle++ (Python version)
# File: c4_02_loop_else.pyc (Python 3.11)

def e01_for_else(xs):
    for x in xs:
        if x > 10:
            break
    else:
        return 'none'
    return x
def e02_while_else(n):
    i = 0
    while i < n:
        if i == 5:
            break
        i += 1
    else:
        return -1
    return i
def e03_shallow_for(xs):
    for x in xs:
        r = x
    r = 0
    return r
def e04_deep(xs, ys):
    for x in xs:
        if x > 0:
            for y in ys:
                if y > x:
                    r = y
                    break
            else:
                r = x
            continue
        r = 0
    return r
def e05_try_host(xs):
    try:
        for x in xs:
            if x:
                r = x
                break
        else:
            r = -1
    finally:
        pass
    return r
def e06_with_host(xs):
    with open('a') as f:
        for x in xs:
            if x == f:
                break
        else:
            r = 0
    return r
def e07_match_host(xs):
    if len(xs) == 0:
        for x in xs:
            r = x
        r = -1
    else:
        r = 1
    return r
class CL:
    def m(self, xs):
        while xs:
            y = xs.pop()
            if y > 3:
                break
        else:
            return None
        return y
def e08_closure(xs):
    def inner():
        for x in xs:
            if x > 1:
                break
        else:
            return 0
        return x
    return inner()
def e09_comp_host(xs):
    return [x for x in xs if x > 1 or x < -1]
