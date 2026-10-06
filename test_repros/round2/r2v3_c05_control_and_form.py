# round-2 r2v3 specimen (synthetic, minimal)
def f(username, uinfo):
    if username in uinfo and not uinfo[username]:
        raise Exception('no user')
    return 1
