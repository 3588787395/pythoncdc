# Source Generated with Decompyle++ (Python version)
# File: rvC_v4.pyc (Python 3.11)

def drain_plain(q, sink):
    out = []
    try:
        while q:
            v = q.pop()
            out.append(v)
    finally:
        sink.append(len(out))
    return out
