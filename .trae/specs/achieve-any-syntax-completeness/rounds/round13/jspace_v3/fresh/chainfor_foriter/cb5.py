def g5(o, x, flag):
    o.attr = f2(x, ('w',) if flag else ())
    for i in range(3):
        x += i
    return o
