def replace_args_simple(match, info):
    match_group_0 = match.group(0)
    param = match.group(1)
    if param not in info:
        return match_group_0
    elif param == 'skip':
        return match_group_0
    else:
        value = info[param]
        if value not in info:
            return match_group_0
        new_val = repr(value)
        return '{}={}'.format(param, new_val)
