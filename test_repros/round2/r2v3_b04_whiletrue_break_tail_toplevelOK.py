# Source Generated with Decompyle++ (Python version)
# File: r2v3_b04_whiletrue_break_tail_toplevel.pyc (Python 3.11)

def f(TH):
    while True:
        if TH:
            break
        time.sleep(0.01)
    event_bus = get_bus()
    return None
