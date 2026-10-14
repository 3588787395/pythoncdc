# Source Generated with Decompyle++ (Python version)
# File: r9a1_07_neg_continue_then_only.pyc (Python 3.11)

def r9a1_07_neg_continue_then_only(q, log, work):
    while len(q) > 0:
        x = q.pop(0)
        if x.skip:
            break
        work(x)
    else:
        sleep(0.001)
