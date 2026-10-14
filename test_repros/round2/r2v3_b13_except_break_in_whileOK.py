# Source Generated with Decompyle++ (Python version)
# File: r2v3_b13_except_break_in_while.pyc (Python 3.11)

def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            pass
        w(is_end, daily)
    return None
