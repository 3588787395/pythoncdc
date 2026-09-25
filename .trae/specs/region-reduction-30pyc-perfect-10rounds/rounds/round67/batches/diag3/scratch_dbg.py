# Source Generated with Decompyle++ (Python version)
# File: r67d3_lostreturn.pyc (Python 3.11)

__doc__ = """r67-diag3 synthetic probe 2: hunt the lost-`return` demotion seen in
flyAccount._do_request (bare Expr + `return None`)."""
def t1(is_async, func, is_dict, error_dict):
    try:
        if is_async:
            if func:
                (error_dict, {} if is_dict else [])
                return None
            else:
                ({'error_no': 'm'}, {} if is_dict else [])
        else:
            return 0
    except Exception:
        return None
def t2(is_async, func, is_dict, error_dict):
    if is_async:
        if func:
            return (error_dict, {} if is_dict else [])
        else:
            return ({'error_no': 'm'}, {} if is_dict else [])
    else:
        return 0
def t3(is_dict, error_dict):
    if error_dict:
        return (error_dict, {} if is_dict else [])
    else:
        return (error_dict, {} if is_dict else [])
def t4(is_dict, error_dict):
    if error_dict:
        return (error_dict, {} if is_dict else [])
    elif is_dict:
        return (error_dict, {} if is_dict else [])
    else:
        return 0
def t5(is_dict, error_dict):
    for k in (1, 2):
        if error_dict:
            return (error_dict, {} if is_dict else [])
    return 0
