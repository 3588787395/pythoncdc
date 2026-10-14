# Source Generated with Decompyle++ (Python version)
# File: r2v3_b03_whilecond_break_tail_in_if.pyc (Python 3.11)

def f(is_end, TH, stop):
    if is_end:
        while not stop:
            if TH:
                break
            time.sleep(0.01)
