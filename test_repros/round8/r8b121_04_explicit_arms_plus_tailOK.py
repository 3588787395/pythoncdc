# Source Generated with Decompyle++ (Python version)
# File: r8b121_04_explicit_arms_plus_tail.pyc (Python 3.11)

def b121_04(log, ex):
    try:
        k(log)
    except Exception as e:
        if log:
            if ex:
                log.a.info(e)
                return None
            log.b.info(e)
            return None
        else:
            return None
    return None
