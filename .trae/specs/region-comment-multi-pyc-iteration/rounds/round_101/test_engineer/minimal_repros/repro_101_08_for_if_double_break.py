# R101-Pattern-C-variant: double break in plain if branch of for loop


def scan(items):
    out = []
    for it in items:
        if it < 0:
            break
            break
        out.append(it)
    return out


def run(items):
    return scan(items)
