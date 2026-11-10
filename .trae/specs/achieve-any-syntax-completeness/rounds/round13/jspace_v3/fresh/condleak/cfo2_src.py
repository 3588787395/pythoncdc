def f(src, dst, length=None, bufsize=None):
    bufsize = bufsize or 16 * 1024
    if length == 0:
        return
    if length is None:
        print(src, dst, bufsize)
        return
    blocks, remainder = divmod(length, bufsize)
    for b in range(blocks):
        print(b)
    if remainder != 0:
        print(remainder)
