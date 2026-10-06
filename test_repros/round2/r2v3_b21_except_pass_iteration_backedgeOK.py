# Source Generated with Decompyle++ (Python version)
# File: r2v3_b21_except_pass_iteration_backedge.pyc (Python 3.11)

def f(items, w):
    for x in items:
        try:
            w(x)
        except ValueError:
            pass
