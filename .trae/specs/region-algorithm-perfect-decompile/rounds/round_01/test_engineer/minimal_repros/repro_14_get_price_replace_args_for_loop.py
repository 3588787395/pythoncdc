def replace_args(match, func, func_info, param_list, param_info,
                 param_value_info, param_value_trans_info_char):
    match_group_0 = match.group(0)
    match_group_1 = match.group(1)
    new_args = []
    new_args.append(match_group_1.split(',')[0])
    for arg in param_list:
        param = arg[0]
        value = arg[1]
        if param in ('frequency', 'fq'):
            value = repr(value)
        elif param in ('fields',) and '[' not in value:
            value = repr(value)
        if param not in param_list:
            return match_group_0
        elif param == 'skip_paused':
            continue
        else:
            pattern = "'([^']*)'|\"([^\"]*)\""
            value_type_change = value
            if '[' in value:
                value_change = eval(value)
                for v in value_change:
                    if param in param_value_info and v not in param_value_info[param]:
                        return match_group_0
            elif param in param_value_info and value_type_change not in param_value_info[param]:
                return match_group_0
            if param in param_value_trans_info_char and value_type_change in param_value_trans_info_char[param]:
                value_type_change = param_value_trans_info_char[param][value_type_change]
                value = repr(value_type_change)
            new_args.append('{}={}'.format(param_info[param], value))
            continue
    return 'func(' + ','.join(new_args) + ')'
