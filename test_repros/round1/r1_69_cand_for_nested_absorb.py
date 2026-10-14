def f69(xs, start, end):
    for n in xs:
        if len(n) == 1:
            if n[0] == start:
                continue
            if n[0] == end:
                pass
        pre = n[0]
        if pre is not None:
            tmp = n[1:]
            if not tmp:
                print('empty')
            else:
                print('full')
        else:
            print('none')
    print('after-loop')
