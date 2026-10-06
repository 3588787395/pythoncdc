# Source Generated with Decompyle++ (Python version)
# File: r2v3_b01_whiletrue_break_tail_in_if.pyc (Python 3.11)

def f(is_end, TH):
    if is_end:
        from mod import THREAD_STATUS
        if THREAD_STATUS:
            pass
    event_bus = get_bus()
    event_bus.publish()
