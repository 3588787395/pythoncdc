def expr_medley(a, b, c):
    lam = lambda x: x + 1
    lc = [x for x in range(3)]
    sc = {x for x in range(3)}
    dc = {x: x for x in range(3)}
    ge = (x for x in range(3))
    fs = f"{a!r:>10} {b} {c}"
    sb = a[1]; sl = a[1:2]
    is1 = a is None; is2 = a is not None
    nt = not a; ng = -a; ps = +a; iv = ~a
    bo = a and b or c; cp = (a < b) <= (b < c)
    tu = (a, b); st = {a, b}; di = {a: b}; li = [a, b]
    at = a.real; ca = lam(a)
    for it in a: pass
    return fs
