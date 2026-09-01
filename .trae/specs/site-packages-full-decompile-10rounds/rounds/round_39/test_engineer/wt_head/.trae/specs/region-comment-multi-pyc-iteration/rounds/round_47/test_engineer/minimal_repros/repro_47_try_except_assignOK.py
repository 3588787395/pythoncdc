# Source Generated with Decompyle++ (Python version)
# File: repro_47_try_except_assign.pyc (Python 3.11)

def func(result_list):
    try:
        result_list.append(1)
    except Exception:
        result_list = []
    else:
        return result_list
