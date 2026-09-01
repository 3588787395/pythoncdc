# Source Generated with Decompyle++ (Python version)
# File: repro_03_try_except_continue.pyc (Python 3.11)

def func(items):
    for item in items:
        try:
            if item > 0:
                continue
            return item
        except Exception:
            continue
