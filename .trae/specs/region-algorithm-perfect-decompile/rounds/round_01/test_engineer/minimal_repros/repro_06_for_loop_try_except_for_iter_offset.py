def for_loop_try_except(items, info):
    new_args = []
    for arg in items:
        param = arg[0]
        value = arg[1]
        try:
            params = eval(param)
            count = str(params[1])
        except:
            count = param.split(',')[1]
        if param in info:
            value = repr(value)
        new_args.append(param + '=' + value)
    return new_args
