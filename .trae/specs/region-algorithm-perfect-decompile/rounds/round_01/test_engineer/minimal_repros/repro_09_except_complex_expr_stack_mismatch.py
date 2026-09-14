def except_complex_expr(data, func_name, param_list):
    try:
        params = eval(data)
        return data
    except:
        if data not in param_list:
            return None
        value = repr(param_list[data])
        return data
