# Source Generated with Decompyle++ (Python version)
# File: r2v3_b07_except_continue_nothing_after_try.pyc (Python 3.11)

def f(q, stop):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            pass
        w(daily)
