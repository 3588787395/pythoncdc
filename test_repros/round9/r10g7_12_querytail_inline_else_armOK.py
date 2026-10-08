# Source Generated with Decompyle++ (Python version)
# File: r10g7_12_querytail_inline_else_arm.pyc (Python 3.11)

def r10g7_12_querytail_inline_else_arm(x, log):
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
            time.sleep(1)
    else:
        y = h(x)
        return None
