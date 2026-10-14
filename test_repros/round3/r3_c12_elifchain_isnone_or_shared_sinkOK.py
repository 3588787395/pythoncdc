# Source Generated with Decompyle++ (Python version)
# File: r3_c12_elifchain_isnone_or_shared_sink.pyc (Python 3.11)

def f(filter_type, short_values, long_values):
    if filter_type == 'all_status':
        return 1
    elif filter_type == 'long_status':
        if not short_values is not None or long_values is None:
            return None
        else:
            return up_v(short_values[-1], long_values[-1])
    elif filter_type == 'short_status' and short_values is not None:
        if long_values is None:
            return None
        else:
            return down_v(short_values[-1], long_values[-1])
    else:
        return None
