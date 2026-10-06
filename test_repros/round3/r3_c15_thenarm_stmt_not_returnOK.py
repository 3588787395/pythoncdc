# Source Generated with Decompyle++ (Python version)
# File: r3_c15_thenarm_stmt_not_return.pyc (Python 3.11)

def f(filter_type, short_values, long_values):
    if filter_type == 'short_status':
        if short_values is None or long_values is None:
            clean()
        return down_v(short_values[-1], long_values[-1])
    else:
        return None
