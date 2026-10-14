# Source Generated with Decompyle++ (Python version)
# File: r8b121_02_with_tail_and_arms.pyc (Python 3.11)

def b121_02(lock, log, ex):
    try:
        with CM(lock):
            do(work)
    except Exception as e:
        if log:
            log.info(e)
