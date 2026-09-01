"""R49 Repro 12: try-except-else with complex control flow"""
def func(return_flag):
    try:
        data = [1, 2, 3]
        status = 'ok'
    except Exception:
        data = []
        status = 'error'
    else:
        if return_flag:
            return ['', '', status]
        else:
            return status
