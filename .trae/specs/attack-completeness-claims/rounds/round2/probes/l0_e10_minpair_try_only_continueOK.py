# Source Generated with Decompyle++ (Python version)
# File: l0_e10_minpair_try_only_continue.pyc (Python 3.11)

__doc__ = 'AT-02/AT-04 最小对 B: try 体只有 continue（无 if）'
def e10(xs):
    for a in xs:
        try:
            print('fin')
        finally:
            print('fin')
