def f106(host, n, name):
    for x in range(n):
        if host(x):
            host('y')
        else:
            return None
        host('tail')
    host('end')
