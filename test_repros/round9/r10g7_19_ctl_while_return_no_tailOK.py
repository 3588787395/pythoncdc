# Source Generated with Decompyle++ (Python version)
# File: r10g7_19_ctl_while_return_no_tail.pyc (Python 3.11)

def r10g7_19_ctl_while_return_no_tail(running, items):
    while running:
        if items:
            return items[0]
        running = step(running)
    return None
