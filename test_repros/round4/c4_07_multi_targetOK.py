# Source Generated with Decompyle++ (Python version)
# File: c4_07_multi_target.pyc (Python 3.11)

def e01_root(x):
    a = b = c = x + 1
    return a + b + c
def e02_shallow(x):
    a = b = x
    return a + b
def e03_deep(x):
    p = 0
    for i in range(3):
        if i:
            p = q = r = i * 2
    return p + q + r
def e04_unpack(x):
    (a, b) = (c, d) = (x, x + 1)
def e05_star_unpack(x):
    a, *b = [x, x + 1, x + 2]
    return (a, b, c, d)
def e06_chain_target(x):
    a = b = [x, x]
    a[0] = x + 1
    b[1] = None
    return a[0] + b[1]
class CMT:
    def m(self, x):
        with open('a') as f:
            p = q = f.read()
        return p + q
def e07_match_host(x):
    match x:
        case 0:
            a = b = x + 1
        case _:
            a = b = 0
    return a + b
def e08_closure(x):
    def inner():
        a = b = x
        return a + b
    return inner()
def e09_attr_chain(x):
    class O:
        pass
    o = O()
    o.a = x
    o.b = None
    return o.a + o.b
