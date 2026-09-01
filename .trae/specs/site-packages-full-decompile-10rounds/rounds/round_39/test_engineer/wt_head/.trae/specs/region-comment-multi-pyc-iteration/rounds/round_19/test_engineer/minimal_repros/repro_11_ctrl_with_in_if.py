def f(p, b):
    if b is not None:
        with open(p, 'r', encoding='utf-8') as fh:
            content = fh.read()
        x = content + '_' + b
    else:
        x = 'default'
    return x
