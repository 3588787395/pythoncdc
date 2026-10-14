def f(filter_type, short_values, long_values):
    if filter_type == 'all_status':
        return 1
    elif filter_type == 'long_status':
        if short_values is None or long_values is None:
            return None
        return up_v(short_values[-1], long_values[-1])
    elif filter_type == 'short_status':
        if short_values is None or long_values is None:
            return None
        return down_v(short_values[-1], long_values[-1])
    return None
