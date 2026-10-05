def f77(xs, start, end):
    def inner(n):
        if n == 1:
            if n == start:
                return 'hit'
            return 'miss'
        return None
    for n in xs:
        if n[0] == 1:
            if n[0] == start:
                print(inner(n))
            if n[0] == end:
                pass
        if n is not None:
            print(n)
        else:
            print('none')
        print('tail-in-loop')
