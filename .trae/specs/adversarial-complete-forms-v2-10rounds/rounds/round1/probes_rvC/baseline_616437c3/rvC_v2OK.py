# Source Generated with Decompyle++ (Python version)
# File: rvC_v2.pyc (Python 3.11)

def drain(q, limit, sink):
    out = []
    try:
        while q:
            v = q.pop()
            if v > limit:
                raise ValueError(v)
            out.append(v)
    finally:
        v = q.pop()
        if v > limit:
            pass
        raise ValueError(v)
        out.append(v)
        q
    return out
