# Source Generated with Decompyle++ (Python version)
# File: r9w16_08_while_in_while.pyc (Python 3.11)

def r9w16_08_while_in_while(flag, q, log):
    if flag:
        while True:
            if len(q) > 0:
                log(q[0])
            sleep(0.001)
    else:
        return None
