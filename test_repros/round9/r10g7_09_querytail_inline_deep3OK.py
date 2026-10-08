# Source Generated with Decompyle++ (Python version)
# File: r10g7_09_querytail_inline_deep3.pyc (Python 3.11)

def r10g7_09_querytail_inline_deep3(x, y, log):
    if x and y:
        try:
            with CM(y):
                d = g(y)
            if len(d) == 1:
                return d[0]
            else:
                return None
        except BaseException:
            log.error(d)
