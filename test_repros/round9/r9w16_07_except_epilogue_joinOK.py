# Source Generated with Decompyle++ (Python version)
# File: r9w16_07_except_epilogue_join.pyc (Python 3.11)

def r9w16_07_except_epilogue_join(q, log):
    while True:
        if len(q) > 0:
            pass
        try:
            x = q.pop(0)
            log(x)
        except ValueError:
            log('err')
        sleep(0.001)
