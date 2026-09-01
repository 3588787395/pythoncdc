# Source Generated with Decompyle++ (Python version)
# File: repro_47_try_except_context.pyc (Python 3.11)

def func(handler):
    result_list = []
    if handler:
        try:
            result_list.append(handler.id)
        except Exception:
            result_list = []
        else:
            return result_list
