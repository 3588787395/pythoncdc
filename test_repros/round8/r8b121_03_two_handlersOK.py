# Source Generated with Decompyle++ (Python version)
# File: r8b121_03_two_handlers.pyc (Python 3.11)

def b121_03(log, ex):
    try:
        k(log)
        return None
    except ValueError as e:
        if log:
            log.a.info(e)
    except TypeError as e:
        if log:
            log.b.info(e)
