def fd_stmt(xs):
    f = lambda x=x: x * 2
    return f


def fd_in_comp(xs):
    return [lambda x=x: x * 2 for x in xs]
