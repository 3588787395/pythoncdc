def guard_try(is_async, is_dict, error_dict):
    try:
        if is_async:
            if error_dict:
                g()
                return error_dict, ({} if is_dict else [])
            else:
                return {'error_no': -1, 'error_info': 'boom'}, ({} if is_dict else [])
        else:
            g2()
            return {'a': 1, 'b': 2}, ([] if is_dict else {})
    except Exception:
        return None


def guard_try_nodict(is_async, is_dict, error_dict):
    try:
        if is_async:
            if error_dict:
                g()
                return error_dict, ({} if is_dict else [])
            else:
                return error_dict, ({} if is_dict else [])
        else:
            return error_dict, ({} if is_dict else [])
    except Exception:
        return None
