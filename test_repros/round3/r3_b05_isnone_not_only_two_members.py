def f(fq, div):
    if fq is None or not div:
        need = 0
    else:
        need = 1
    for t in TYPES:
        use(need, t)
    return need
