# Source Generated with Decompyle++ (Python version)
# File: r76_b1a_jqcond.pyc (Python 3.11)

import re
def func_get_bars_convert_code(code):
    func = 'get_bars'
    pattern = '\\bget_bars\\((.*)\\)'
    param_list = ['unit', 'fields', 'include_now', 'end_dt', 'fq_ref_date']
    def replace_args(match):
        match_group_0 = remove_space_in_function_call(match.group(0))
        match_group_1 = remove_space_in_function_call(match.group(1))
        key_params_info_list, key_params_info_init_dict = parse_function_args(match_group_1)
        key_params_info_lenth = len(key_params_info_list)
        if key_params_info_lenth != 5:
            user_log.info('转换失败！%s函数实际入参数量与标准入参数量不符' % func)
            return match_group_0
        position_params_info = match_group_1.split(',unit')[0]
        try:
            params = eval(position_params_info)
            stock = params[0]
            if "'" not in stock:
                stock = repr(stock)
            count = str(params[1])
        except:
            stock_tmp = position_params_info.split(',')[0]
            count_tmp = position_params_info.split(',')[1]
            if ')' not in stock_tmp or '[' in stock_tmp and ']' not in stock_tmp:
                count = position_params_info.split(',')[-1]
                stock = position_params_info.replace(count, '')
                stock = stock[:-1]
            else:
                stock = stock_tmp
                count = count_tmp
        new_args = []
        new_args_get_history = []
        new_args_get_history.append(count)
        new_args_get_price = []
        new_args_get_price.append(stock)
        flag = 'get_history'
        for arg in key_params_info_list:
            param = arg[0]
            value = arg[1]
            if param == 'end_dt':
                if value == 'None':
                    flag = 'get_history'
                    continue
                flag = 'get_price'
        if flag == 'get_history':
            new_args = new_args_get_history
            new_args.append('security_list={}'.format(stock))
            param_info = {'unit': 'frequency', 'fields': 'field', 'include_now': 'include', 'fq_ref_date': 'fq'}
            param_value_info = {'unit': ['1m', '5m', '15m', '30m', '60m', '120m', '1d', '1w', '1M'], 'fields': ['open', 'close', 'high', 'low', 'volume', 'money'], 'include_now': ['True', 'False']}
            param_value_trans_info_char = {'fq_ref_date': {'None': 'None'}}
            for arg in key_params_info_list:
                param = arg[0]
                value = arg[1]
                if param == 'end_dt':
                    continue
                elif param in ('unit',):
                    value = repr(value)
                elif param in ('fields',) and '[' not in value:
                    value = repr(value)
                if param not in param_list:
                    user_log.info(f'转换失败！{func!s}函数{param!s}字段入参必须在{param_list!s}中')
                    return match_group_0
                else:
                    pattern = '\'([^\\\']+)\'|\\"([^\\"]+)\\"'
                    value_type_change = re.sub(pattern, lambda x: x.group(1) or x.group(2), value)
                    if '[' in value:
                        value_change = eval(value)
                        for v in value_change:
                            if param in param_value_info and v not in param_value_info[param]:
                                user_log.info(f'转换失败！{func!s}函数{param!s}字段入参的值必须在{param_value_info[param]!s}中才能转换')
                                return match_group_0
                    elif param in param_value_info and value_type_change not in param_value_info[param]:
                        user_log.info(f'转换失败！{func!s}函数{param!s}字段入参的值必须在{param_value_info[param]!s}中才能转换')
                        return match_group_0
                    if param in param_value_trans_info_char:
                        if value_type_change in param_value_trans_info_char[param]:
                            value_type_change = param_value_trans_info_char[param][value_type_change]
                            value = value
                        else:
                            value = repr('dypre')
                new_args.append('{}={}'.format(param_info[param], value))
            user_log.info('转换成功！%s函数转换完成，转换后函数名变成get_history' % func)
            return 'get_history(' + ','.join(new_args) + ')'
        elif flag == 'get_price':
            new_args = new_args_get_price
            new_args.append('count={}'.format(count))
            param_info = {'unit': 'frequency', 'fields': 'fields', 'fq_ref_date': 'fq', 'end_dt': 'end_date'}
            param_value_info = {'unit': ['1m', '5m', '15m', '30m', '60m', '120m', '1d', '1w', '1M'], 'fields': ['open', 'close', 'high', 'low', 'volume', 'money'], 'include_now': ['True']}
            param_value_trans_info_char = {'fq_ref_date': {'None': 'None'}}
            for arg in key_params_info_list:
                param = arg[0]
                value = arg[1]
                if param in ('unit',):
                    value = repr(value)
                elif param in ('fields',) and '[' not in value:
                    value = repr(value)
                if param not in param_list:
                    user_log.info(f'转换失败！{func!s}函数{param!s}字段入参必须在{param_list!s}中')
                    return match_group_0
                else:
                    pattern = '\'([^\\\']+)\'|\\"([^\\"]+)\\"'
                    value_type_change = re.sub(pattern, lambda x: x.group(1) or x.group(2), value)
                    if '[' in value:
                        value_change = eval(value)
                        for v in value_change:
                            if param in param_value_info and v not in param_value_info[param]:
                                user_log.info(f'转换失败！{func!s}函数{param!s}字段入参的值必须在{param_value_info[param]!s}中才能转换')
                                return match_group_0
                    elif param in param_value_info and value_type_change not in param_value_info[param]:
                        user_log.info(f'转换失败！{func!s}函数转换成PTrade的get_price函数场景下，{param!s}字段入参的值必须在{param_value_info[param]!s}中才能转换')
                        return match_group_0
                    if param in param_value_trans_info_char:
                        if value_type_change in param_value_trans_info_char[param]:
                            value_type_change = param_value_trans_info_char[param][value_type_change]
                            value = value
                        else:
                            value = repr('dypre')
                    if param == 'include_now':
                        continue
                    new_args.append('{}={}'.format(param_info[param], value))
                    continue
            user_log.info('转换成功！%s函数转换完成，转换后函数名变成get_price' % func)
            return 'get_price(' + ','.join(new_args) + ')'
    new_code = re.sub(pattern, replace_args, code)
    return new_code
