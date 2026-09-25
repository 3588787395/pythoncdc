def guard_tuple_return(is_dict, error_dict):
    return error_dict, ({} if is_dict else [])


def guard_dict_tuple_return(is_dict):
    return {'error_no': -1, 'error_info': 'boom'}, ({} if is_dict else [])


def guard_plain_dict_return(is_dict):
    d = {'error_no': -1, 'error_info': 'boom'}
    return d, ({} if is_dict else [])
