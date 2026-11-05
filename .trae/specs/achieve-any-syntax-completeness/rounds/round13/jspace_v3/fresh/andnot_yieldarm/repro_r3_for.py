def k(toks, ns, pa):
    for tok in toks:
        tag = tok
        if tag and tag[0] != '{':
            if ':' in tag:
                yield ('c', tag)
            elif ns and not pa:
                yield ('n', ns)
            else:
                yield tok
            pa = False
        else:
            yield tok
            pa = tag == '@'
