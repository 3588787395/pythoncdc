# R101-Pattern-B-simple: for + if+continue only (R100-fixed shape, control)


def keep(items):
    out = []
    for it in items:
        if it % 2 == 0:
            continue
        out.append(it)
    return out


def run(items):
    return keep(items)
