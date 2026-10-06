def f(s):
    d = mk_frame()
    parts = s.split('.')
    if len(parts) != 2:
        return d
    code = parts[0]
    if parts[1] == 'SS':
        dir_ = 'XSHG'
    elif parts[1] == 'SZ':
        dir_ = 'XSHE'
    else:
        return d
    rows = read_csv(dir_, code)
    return rows
