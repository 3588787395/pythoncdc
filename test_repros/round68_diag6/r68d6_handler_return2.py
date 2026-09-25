def h4(x, is_dict):
    try:
        f()
    except BaseException as e:
        result = {} if is_dict else []
        return {'error_no': x, 'error_info': 'e'}, result


def h5(x, is_dict):
    try:
        f()
    except BaseException as e:
        print(e)
        result = {} if is_dict else []
        return {'error_no': x, 'error_info': 'e'}, result
