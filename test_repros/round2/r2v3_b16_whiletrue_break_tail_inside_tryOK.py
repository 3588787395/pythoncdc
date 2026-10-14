# Source Generated with Decompyle++ (Python version)
# File: r2v3_b16_whiletrue_break_tail_inside_try.pyc (Python 3.11)

def f(is_end, TH):
    try:
        while True:
            if TH:
                break
            time.sleep(0.01)
    except ValueError:
        log('e')
    event_bus = get_bus()
