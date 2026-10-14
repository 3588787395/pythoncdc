# Source Generated with Decompyle++ (Python version)
# File: r8nop_14_flytools_mini_arm_returns.pyc (Python 3.11)

def n8p14(a, log):
    try:
        with CM(a), open(a) as fp:
            r = rd(fp)
        w(fa(r))
    except Exception as e:
        if log:
            if r:
                log.info(e)
            elif not r:
                log.warn(e)
