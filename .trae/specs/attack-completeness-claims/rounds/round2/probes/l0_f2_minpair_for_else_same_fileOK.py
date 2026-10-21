# Source Generated with Decompyle++ (Python version)
# File: l0_f2_minpair_for_else_same_file.pyc (Python 3.11)

__doc__ = 'AT-04 同文件最小对：n1（for-else 被塌陷）与 n2（无 else）对照'
def n1(items, g):
    for x in items:
        try:
            if x:
                break
            g(x)
        finally:
            g(0)
def n2(items, g):
    for x in items:
        try:
            if x:
                break
            g(x)
        finally:
            g(0)
        g(1)
