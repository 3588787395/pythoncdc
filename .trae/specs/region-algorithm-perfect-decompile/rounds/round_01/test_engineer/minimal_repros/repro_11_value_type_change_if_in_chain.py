def value_type_change_pattern(param, value_info, trans_info, value):
    try:
        params = eval(param)
        stock = params[0]
        count = str(params[1])
    except:
        count = param.split(',')[1]
        stock = param.split(',')[0]
    if param in value_info and value not in value_info[param]:
        return None
    if param in trans_info and value in trans_info[param]:
        value = trans_info[param][value]
        value = repr(value)
    return value
