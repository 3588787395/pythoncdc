# round-2 r2v3 specimen (synthetic, minimal)
def f(username, uinfo):
    if username in uinfo and uinfo[username]:
        return 1
    raise Exception('no user')
