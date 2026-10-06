# Source Generated with Decompyle++ (Python version)
# File: r2v3_b02_whiletrue_break_no_tail.pyc (Python 3.11)

def f(is_end, TH):
    if is_end:
        while True:
            if TH:
                break
    event_bus = get_bus()
    event_bus.publish()
