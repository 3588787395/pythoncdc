# Source Generated with Decompyle++ (Python version)
# File: E1_e2_shape.pyc (Python 3.11)

def w(toks, ns, pa):
    it = iter(toks)
    tok = next(it, None)
    while tok is not None:
        if tok == 'a':
            yield ('a', tok)
        elif ns and not pa:
            yield ('n', ns)
        else:
            yield tok
        tok = next(it, None)
