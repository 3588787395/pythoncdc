# Source Generated with Decompyle++ (Python version)
# File: mix.pyc (Python 3.11)

def b1(xs, ys, zs):
    return [(x, y, z) for x in xs for y in ys for z in zs]
def b2(xs, ys):
    return [x for x in xs for y in ys]
class K:
    def m(self, xs):
        while xs:
            y = xs.pop()
            if y > 3:
                break
        return None
def c1(xs):
    while xs:
        y = xs.pop()
        if y > 3:
            break
    return None
def d1(a, b):
    with open(a) as f, open(b) as g:
        return f.read() + g.read()
        return None
def d2(a):
    with open(a) as f:
        return f.read()
