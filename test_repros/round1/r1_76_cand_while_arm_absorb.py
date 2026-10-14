def f76(xs, start, end):
    n = 0
    while n < 5:
        n += 1
        if n == 1:
            if n == start:
                continue
            if n == end:
                pass
        if n is not None:
            print(n)
        else:
            print('none')
        print('tail-in-loop')
