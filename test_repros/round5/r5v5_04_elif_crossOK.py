# Source Generated with Decompyle++ (Python version)
# File: r5v5_04_elif_cross.pyc (Python 3.11)

class EClass:
    S = 4
    if S == 1:
        V = 'a'
    elif S == 2:
        V = 'b'
    elif S == 3:
        V = 'c'
    elif S == 4:
        V = 'd'
    else:
        V = 'e'
    def m(self, x):
        for i in range(3):
            if x == i:
                r = 'a'
                continue
            if x == i + 1:
                r = 'b'
                continue
            if x == i + 2:
                r = 'c'
                continue
            r = 'd'
            continue
        return r
def efn_root(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    elif x == 3:
        return 'c'
    else:
        return 'z'
def efn_deep(x, y, z):
    r = 0
    while x > 0:
        if y > 0:
            if z == 1:
                r = 1
            elif z == 2:
                r = 2
            else:
                r = 3
        elif y < 0:
            if z == 1:
                r = 4
            elif z == 2:
                r = 5
            else:
                r = 6
        else:
            r = 7
        x -= 1
    return r
_GE = 3
if _GE > 1:
    _GR = 'a'
elif _GE > 2:
    _GR = 'b'
elif _GE > 3:
    _GR = 'c'
else:
    _GR = 'd'
