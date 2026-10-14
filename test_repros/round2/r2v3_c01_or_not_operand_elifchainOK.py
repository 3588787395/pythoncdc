# Source Generated with Decompyle++ (Python version)
# File: r2v3_c01_or_not_operand_elifchain.pyc (Python 3.11)

def f(username, future_code, finfo, uinfo):
    if future_code not in finfo:
        raise Exception('no code')
    elif username not in uinfo or not uinfo[username]:
        raise Exception('no user')
    elif future_code not in uinfo[username]:
        raise Exception('no perm')
    else:
        out = finfo[future_code].copy()
        out.update(uinfo[username][future_code])
        return out
