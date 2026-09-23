def w(g, first_stock, first_future):
    sa = g(1)
    fa = g(2)
    sm = None
    fm = None
    try:
        sm = g(3)
    except BaseException:
        c = False
        sa = g(4)
        while first_stock != sa:
            try:
                sm = g(5)
                c = True
                break
            except Exception as e:
                sa = g(6)
        if not c:
            return (None, 1)
    try:
        fm = g(7)
    except BaseException:
        c = False
        fa = g(8)
        while first_future != fa:
            try:
                fm = g(9)
                c = True
                break
            except Exception as e:
                fa = g(10)
        if not c:
            return (None, 2)
    return (sm, fm)
