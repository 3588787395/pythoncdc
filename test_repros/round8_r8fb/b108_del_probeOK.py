# Source Generated with Decompyle++ (Python version)
# File: b108_del_probe.pyc (Python 3.11)

def e01_del_finally(x):
    try:
        r = x + 1
    finally:
        del x
    return r
def e02_del_except(x):
    try:
        g()
    except E as e:
        del x
    return 0
def e03_del_finally_attr(o):
    try:
        r = o.a
    finally:
        del o.a
    return r
