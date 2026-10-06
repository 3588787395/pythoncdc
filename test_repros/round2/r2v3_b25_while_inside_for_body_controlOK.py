# Source Generated with Decompyle++ (Python version)
# File: r2v3_b25_while_inside_for_body_control.pyc (Python 3.11)

def f(items, TH):
    for x in items:
        while True:
            if TH:
                break
            time.sleep(0.01)
    g()
