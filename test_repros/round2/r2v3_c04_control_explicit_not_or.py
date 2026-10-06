# round-2 r2v3 specimen (synthetic, minimal)
def f(username, uinfo):
    if not (username not in uinfo or uinfo[username]):
        raise Exception('no user')
    return 1
