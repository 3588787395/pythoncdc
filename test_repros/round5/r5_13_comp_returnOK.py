# Source Generated with Decompyle++ (Python version)
# File: r5_13_comp_return.pyc (Python 3.11)

def rt_two_comps(xs, ys):
    a = [x for x in xs]
    b = [y for y in ys]
    return (a, b)
def rt_three_forms(xs, pairs):
    lc = [x * 2 for x in xs]
    dc = {k: v for k, v in pairs}
    ge = sum((v for v in xs))
    return (lc, dc, ge)
def rt_early(xs, flag):
    if flag:
        return [x for x in xs]
    else:
        return [x + 1 for x in xs]
def rt_genexp_return(xs):
    return (x for x in xs)
def rt_nested_return(mat):
    return [[y for y in r] for r in mat]
def rt_comp_and_loop(xs):
    out = [x for x in xs]
    total = 0
    for v in out:
        total += v
    return (out, total)
