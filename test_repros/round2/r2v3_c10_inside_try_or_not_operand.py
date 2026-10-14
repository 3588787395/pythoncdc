# round-2 r2v3 specimen (synthetic, minimal)
def f(username, uinfo):
    try:
        if username not in uinfo or not uinfo[username]:
            raise Exception('no user')
    except Exception as e:
        log(e)
    return 1
