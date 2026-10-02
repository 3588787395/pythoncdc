def c_single_if(xs):
    return [x for x in xs if x > 0]


def c_double_if(xs):
    return [x for x in xs if x > 0 if x % 2 == 0]


def c_ifelse_body(xs):
    return [x if x > 0 else -x for x in xs]


def c_cross_for(a, b):
    return [x + y for x in a for y in b if x < y]


def c_between_fors(a, b, c):
    return [x + y + z for x in a if x for y in b if y for z in c]


def sc_cond_set(xs):
    return {x for x in xs if x >= 0}
