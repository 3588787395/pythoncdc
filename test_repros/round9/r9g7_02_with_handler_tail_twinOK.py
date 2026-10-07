# Source Generated with Decompyle++ (Python version)
# File: r9g7_02_with_handler_tail_twin.pyc (Python 3.11)

def g7_02(lock, log, ex):
    try:
        with CM(lock):
            do(work)
    except Exception as e:
        log.info(e)
        return None
