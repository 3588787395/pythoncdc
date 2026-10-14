# Source Generated with Decompyle++ (Python version)
# File: r9g7_04_mixed_elsearm_and_tail.pyc (Python 3.11)

def g7_04(lock, log, bars):
    if bars:
        if log:
            return bars[0]
        else:
            return None
    try:
        with CM(lock):
            do(work)
            return None
    except Exception as e:
        log.info(e)
        return None
