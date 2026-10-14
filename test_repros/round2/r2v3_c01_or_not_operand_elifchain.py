# round-2 r2v3 specimen (synthetic, minimal)
def f(username, future_code, finfo, uinfo):
    if future_code not in finfo:
        raise Exception('no code')
    elif username not in uinfo or not uinfo[username]:
        raise Exception('no user')
    elif future_code not in uinfo[username]:
        raise Exception('no perm')
    out = finfo[future_code].copy()
    out.update(uinfo[username][future_code])
    return out
