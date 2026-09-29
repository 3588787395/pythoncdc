# Source Generated with Decompyle++ (Python version)
# File: b_try_for_break_last.pyc (Python 3.11)

def b_try_for_break_last(items):
    hit = 0
    try:
        for it in items:
            if it:
                hit += 1
            else:
                break
    except BaseException:
        return -1
    return hit
