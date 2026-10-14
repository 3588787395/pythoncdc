# Source Generated with Decompyle++ (Python version)
# File: r2v3_b11_except_continue_inside_with.pyc (Python 3.11)

def f(q, stop, w, fp):
    while not stop:
        with fp:
            is_end, daily = q.get(timeout=1)
            if ValueError:
                pass
            continue
            w(is_end, daily)
            break
