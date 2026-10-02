def n_matrix(mat):
    return [[y for y in row] for row in mat]


def n_flatten(mat):
    return [y for row in mat for y in row]


def n_dict_inner(groups):
    return {k: [v * 2 for v in vals] for k, vals in groups}


def n_args(a, b):
    return sorted([x for x in a]), sum([y for y in b])


def n_deep(cube):
    return [[[z for z in col] for col in row] for row in cube]


def n_genexp_inner(mat):
    return [sum(y for y in row) for row in mat]
