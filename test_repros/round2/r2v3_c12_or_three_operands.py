# round-2 r2v3 specimen (synthetic, minimal)
def f(a, b, c, out):
    if a not in b or not b[a] or c is None:
        raise Exception('bad')
    return out
