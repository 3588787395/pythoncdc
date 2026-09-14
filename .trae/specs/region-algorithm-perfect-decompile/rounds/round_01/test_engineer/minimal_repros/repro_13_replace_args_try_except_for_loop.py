def replace_args(match, func, func_info, param_list, param_info,
                 param_value_info, param_value_trans_info_char, param_value_trans_info_bool,
                 position_params_info):
    match_group_0 = match.group(0)
    match_group_1 = match.group(1)
    new_args = []
    new_args.append(position_params_info.split(',')[0])
    try:
        params = eval(position_params_info)
        stock = params[0]
        if "'" not in stock:
            stock = repr(stock)
        count = str(params[1])
    except:
        stock_tmp = position_params_info.split(',')[0]
        count_tmp = position_params_info.split(',')[1]
        if ')' not in stock_tmp or '[' in stock_tmp:
            if ']' not in stock_tmp:
                count = position_params_info.split(',')[-1]
                stock = position_params_info.replace(count, '')
                stock = stock[:-1]
            else:
                stock = stock_tmp
                count = count_tmp
    new_args.append(count)
    new_args.append('security_list={}'.format(stock))
    for arg in param_list:
        param = arg[0]
        value = arg[1]
        if param not in param_list:
            return match_group_0
        elif param == 'skip_paused':
            continue
        else:
            pattern = "'([^']*)'|\"([^\"]*)\""
            value_type_change = value
            if param in param_value_info and value_type_change not in param_value_info[param]:
                return match_group_0
            if param in param_value_trans_info_char and value_type_change in param_value_trans_info_char[param]:
                value_type_change = param_value_trans_info_char[param][value_type_change]
                value = repr(value_type_change)
            if param in param_value_trans_info_bool and value_type_change in param_value_trans_info_bool[param]:
                value_type_change = param_value_trans_info_bool[param][value_type_change]
                value = repr(value_type_change)
            new_args.append('{}={}'.format(param_info[param], value))
            continue
    return 'func(' + ','.join(new_args) + ')'
