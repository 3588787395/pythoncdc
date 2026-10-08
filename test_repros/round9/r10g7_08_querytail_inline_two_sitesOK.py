# Source Generated with Decompyle++ (Python version)
# File: r10g7_08_querytail_inline_two_sites.pyc (Python 3.11)

def r10g7_08_querytail_inline_two_sites(x, y, log):
    if x:
        try:
            with CM(x):
                d = g(x)
            if len(d) == 1:
                return d[0]
            else:
                return None
        except BaseException:
            log.error(d)
    if y:
        pass
    else:
        return None
    if y:
        try:
            with CM(y):
                e = h(y)
            if len(e) == 2:
                return e[0]
            else:
                return None
        except BaseException:
            log.error(e)
