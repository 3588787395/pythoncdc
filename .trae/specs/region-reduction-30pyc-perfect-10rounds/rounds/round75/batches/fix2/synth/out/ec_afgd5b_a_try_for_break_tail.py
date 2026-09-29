# Source Generated with Decompyle++ (Python version)
# File: a_try_for_break_tail.pyc (Python 3.11)

def a_try_for_break_tail(items, log):
    hit = 0
    try:
        with open('nul') as fh:
            for it in items:
                if it < 0:
                    break
                hit += it
    except BaseException:
        return -1
    del items
    log.append(hit)
    return hit
