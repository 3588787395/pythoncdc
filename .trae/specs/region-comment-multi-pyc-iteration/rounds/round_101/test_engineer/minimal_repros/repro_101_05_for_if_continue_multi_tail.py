# R101-Pattern-B-variant: for + if+continue + multiple trailing statements


def collect(items, skip):
    out = []
    total = 0
    for it in items:
        if it == skip:
            continue
        out.append(it)
        total += 1
    return out, total


def run(items, skip):
    return collect(items, skip)
