def f(a, b, c, d):
    if a or not b or isinstance(c, str) and d:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
