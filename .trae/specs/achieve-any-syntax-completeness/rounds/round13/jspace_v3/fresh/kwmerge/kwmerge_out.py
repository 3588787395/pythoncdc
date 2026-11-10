# Source Generated with Decompyle++ (Python version)
# File: kwmerge.pyc (Python 3.11)

def f(member, new_attrs):
    return member.replace(**new_attrs, deep=False)
def g(d, kw):
    return d.call(**kw, x=1, y=2)
def h(d, a, b):
    return d.call(**a, **b)
