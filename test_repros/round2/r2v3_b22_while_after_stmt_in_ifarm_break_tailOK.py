# Source Generated with Decompyle++ (Python version)
# File: r2v3_b22_while_after_stmt_in_ifarm_break_tail.pyc (Python 3.11)

def f(is_end, TH):
    if is_end:
        bus = get_bus()
        while True:
            if TH:
                break
            time.sleep(0.01)
    publish(bus)
