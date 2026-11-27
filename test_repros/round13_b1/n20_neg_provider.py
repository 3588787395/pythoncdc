def n20_walrus_spec(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{(q := w):>{(r := w)}}'
    return ''


def n20_starred_spec(a, w):
    for i in range(3):
        if i:
            while i:
                return f'{len(w):>{max(*w)}}'
    return 0
