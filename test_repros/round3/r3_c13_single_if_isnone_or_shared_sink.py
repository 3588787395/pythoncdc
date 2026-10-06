def f(filter_type, short_values, long_values):
    if filter_type == 'short_status':
        if short_values is None or long_values is None:
            return None
        return down_v(short_values[-1], long_values[-1])
    return None
