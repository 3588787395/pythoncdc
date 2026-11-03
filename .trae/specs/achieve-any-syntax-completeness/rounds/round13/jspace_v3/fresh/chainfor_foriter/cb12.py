def g12(lst, x, flag):
    lst[0] = g3(x, 1 if flag else 2)
    for i in lst:
        yield i
