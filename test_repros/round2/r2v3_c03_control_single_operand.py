# round-2 r2v3 specimen (synthetic, minimal)
def f(username, uinfo):
    if username not in uinfo:
        raise Exception('no user')
    return 1
