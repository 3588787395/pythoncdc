def f68(xs, start, end):
    for n in xs:
        if n[0] == 1:
            if n[0] == start:
                continue
            if n[0] == end:
                pass
        if n is not None:
            print(n)
        else:
            print('none')
        print('tail-in-loop')
    print('after-loop')
