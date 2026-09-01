def f(p):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    return content
