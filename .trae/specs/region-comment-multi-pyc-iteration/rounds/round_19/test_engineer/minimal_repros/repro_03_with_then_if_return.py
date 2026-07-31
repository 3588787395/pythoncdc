def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if b is None:
        return 'none'
    return b + '_tail'
