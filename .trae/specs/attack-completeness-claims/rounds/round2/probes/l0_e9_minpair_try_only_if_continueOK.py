# Source Generated with Decompyle++ (Python version)
# File: l0_e9_minpair_try_only_if_continue.pyc (Python 3.11)

__doc__ = 'AT-02/AT-04 最小对 A: try 体只有 if+continue（无后续语句）'
def e9(items, g):
    for x in items:
        try:
            if x:
                continue
            g(0)
            continue
        finally:
            g(0)
