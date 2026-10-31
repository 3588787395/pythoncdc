# Source Generated with Decompyle++ (Python version)
# File: pd8.pbpyc (Python 3.11)

def f(items, opt):
    m = {k: len(k) for k in items}
    m['total'] = sum(m.values())
    w = dict(m)
    r = wrap(payload=m or w, tag=opt or 'z')
    return r
