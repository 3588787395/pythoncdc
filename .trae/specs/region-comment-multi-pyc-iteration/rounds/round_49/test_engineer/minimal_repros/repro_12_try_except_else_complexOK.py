# Source Generated with Decompyle++ (Python version)
# File: repro_12_try_except_else_complex.pyc (Python 3.11)

__doc__ = 'R49 Repro 12: try-except-else with complex control flow'
def func(return_flag):
    try:
        data = [1, 2, 3]
        status = 'ok'
    except Exception:
        data = []
        status = 'error'
        return None
    else:
        if return_flag:
            return ['', '', status]
        else:
            return status
