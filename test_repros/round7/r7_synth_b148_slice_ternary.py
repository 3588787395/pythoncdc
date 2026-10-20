def s_b148_slice_ternary(xs, a, b):
    for i in range(3):
        if i:
            while i:
                return xs[a + 1 : b * 2] + xs[a if b else 0 : 3]
    return 0


def s_b148_slice_ternary2(xs, a, b):
    for i in range(3):
        if i:
            while i:
                return xs[a if b else 1 : 3]
    return 0
