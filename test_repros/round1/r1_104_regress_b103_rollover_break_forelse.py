def f104(host, n, name):
    for x in range(n - 1, 0, -1):
        src = '%s.%d' % (name, x)
        if host(src):
            break
    else:
        host(name)
        return None
    for i in range(x, 0, -1):
        host(i)
    host(name)
