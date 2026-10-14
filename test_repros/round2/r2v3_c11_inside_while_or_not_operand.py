# round-2 r2v3 specimen (synthetic, minimal)
def f(q, uinfo):
    while q:
        username = q.pop()
        if username not in uinfo or not uinfo[username]:
            continue
        use(username)
