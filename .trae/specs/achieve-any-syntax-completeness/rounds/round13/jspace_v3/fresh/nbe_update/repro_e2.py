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
