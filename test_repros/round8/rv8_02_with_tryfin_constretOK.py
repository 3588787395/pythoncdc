# Source Generated with Decompyle++ (Python version)
# File: rv8_02_with_tryfin_constret.pyc (Python 3.11)

def tryfin_return_str():
    try:
        pass
    finally:
        pass
    return 'done'
def tryfin_return_negative():
    try:
        pass
    finally:
        pass
    return -42
def tryfin_then_more(x):
    try:
        pass
    finally:
        pass
def with_body_tryfin_chain(p):
    with open(p) as fh:
        try:
            pass
        finally:
            pass
    return fh
def try_except_fin_nonempty(x):
    try:
        v = int(x)
    except ValueError:
        v = 0
    finally:
        v = v + 1
    return v
def while_chain_subscript(xs, n):
    out = {}
    i = 0
    while i < n:
        out[i] = out['last'] = xs[i]
        i += 1
    return out
