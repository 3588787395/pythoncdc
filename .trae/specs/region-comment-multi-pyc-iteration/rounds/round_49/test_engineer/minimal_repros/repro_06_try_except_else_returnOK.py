# Source Generated with Decompyle++ (Python version)
# File: repro_06_try_except_else_return.pyc (Python 3.11)

__doc__ = 'R49 Repro 06: try-except-else with return in else'
def func():
    try:
        x = 3
        return x
    except Exception:
        x = 0
        return None
