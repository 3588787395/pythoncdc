# Source Generated with Decompyle++ (Python version)
# File: r10g7_13_probe_valuetail_multiminute.pyc (Python 3.11)

def r10g7_13_probe_valuetail_multiminute(mode, running, log):
    if mode == 1 and running:
        while running:
            try:
                r = g(running)
            except BaseException:
                log(r)
            running = nxt(running)
    else:
        res = other(mode)
    return res
