def f(rows, opt):
    idx = {r[0]: r[1] for r in rows}
    idx['meta'] = True
    holder = Box()
    holder.data = idx
    out = transform(src=holder, mode=opt or 'fast')(idx)
    return out
