# Source Generated with Decompyle++ (Python version)
# File: r2v3_b19_except_continue_nested_while.pyc (Python 3.11)

def f(q, stop, w):
    while not stop:
        while q:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
        log('outer')
