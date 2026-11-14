def f(host, port, names):
    if not host or (not port and host in names):
        return 1
    return 0
