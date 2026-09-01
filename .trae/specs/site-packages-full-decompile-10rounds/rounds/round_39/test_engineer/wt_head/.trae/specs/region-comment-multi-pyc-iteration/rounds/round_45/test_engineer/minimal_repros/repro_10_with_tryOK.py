# Source Generated with Decompyle++ (Python version)
# File: repro_10_with_try.pyc (Python 3.11)

def func(lock):
    with lock:
        try:
            return 1
        except Exception:
            return 0
