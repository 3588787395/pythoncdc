# ne01: G1 负对照——平坦均匀链与已知工作分组形态（预期 MATCH）
def n_flat_or(a, b, c):
    for i in range(3):
        if i:
            return a or b or c
    return 0


def n_flat_and(a, b, c):
    for i in range(3):
        if i:
            return a and b and c
    return 0


def n_grouped_pair(a, b, c, d):
    for i in range(3):
        if i:
            return (a or b) and (c or d)
    return 0


def n_simple_two(a, b):
    for i in range(3):
        if i:
            return a and b
    return 0
