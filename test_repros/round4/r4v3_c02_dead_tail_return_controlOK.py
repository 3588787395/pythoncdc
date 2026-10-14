# Source Generated with Decompyle++ (Python version)
# File: r4v3_c02_dead_tail_return_control.pyc (Python 3.11)

def f(s):
    d = mk_frame()
    parts = s.split('.')
    if len(parts) != 2:
        return d
    else:
        code = parts[0]
        if parts[1] == 'SS':
            dir_ = 'XSHG'
        elif parts[1] == 'SZ':
            dir_ = 'XSHE'
        else:
            return d
        rows = read_csv(dir_, code)
        return rows
