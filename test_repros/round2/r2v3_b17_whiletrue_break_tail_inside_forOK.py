# Source Generated with Decompyle++ (Python version)
# File: r2v3_b17_whiletrue_break_tail_inside_for.pyc (Python 3.11)

def f(items, TH):
    for it in items:
        while True:
            if TH:
                break
            time.sleep(0.01)
    event_bus = get_bus()
