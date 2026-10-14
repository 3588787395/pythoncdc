# Source Generated with Decompyle++ (Python version)
# File: r3_c14_single_if_isnone_and_shared_sink.pyc (Python 3.11)

def f(filter_type, short_values, long_values):
    if filter_type == 'short_status':
        if short_values is None and long_values is None:
            return None
        return down_v(short_values[-1], long_values[-1])
    else:
        return None
