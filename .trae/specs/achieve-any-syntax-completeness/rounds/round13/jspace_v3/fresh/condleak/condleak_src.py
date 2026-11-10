def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    print(bufsize, length)
