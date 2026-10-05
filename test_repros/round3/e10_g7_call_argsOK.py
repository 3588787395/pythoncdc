# Source Generated with Decompyle++ (Python version)
# File: e10_g7_call_args.pyc (Python 3.11)

class Chain:
    def a(self):
        return self
    def b(self):
        return self
    def c(self):
        return 1
def f_kwargs_mixed(a, b, c, d):
    def sink(w, x, y=0, z=0):
        return w + x + y + z
    for i in range(3):
        if i and i:
            return sink(a, b, y=c, z=d)
    return 0
def f_starargs_mixed(a, rest):
    def sink(x, *rs):
        return x + sum(rs)
    for i in range(3):
        if i and i:
            return sink(a, 3, *(rest))
    return 0
def f_dstar_mixed(a, kw):
    def sink(x, b=0, c=0):
        return x + b + c
    for i in range(3):
        if i and i:
            return sink(a, b=1, **(kw))
    return 0
def f_both_star_dstar(a, rest, kw):
    def sink(x, *rs, y=0, **ks):
        return x + sum(rs) + y + len(ks)
    for i in range(3):
        if i and i:
            return sink(a, y=2, *(rest), **(kw))
    return 0
def f_call_chain(a):
    def h(x):
        return x - 1
    def g(x):
        return x * 2
    for i in range(3):
        if i and i:
            return h(g(h(a)))
    return 0
def f_method_chain(a):
    obj = Chain()
    for i in range(3):
        if i and i:
            return obj.a().b().c() + a
    return 0
def f_call_lambda_arg(a):
    for i in range(3):
        if i and i:
            return sorted([a, 2, 1], key=lambda x: -x)
    return 0
def f_call_comp_arg(xs):
    for i in range(3):
        if i and i:
            return sum([x for x in xs], 10)
    return 0
def f_deco_with_args(a):
    def deco(n):
        def wrap(fn):
            def inner(x):
                return fn(x) + n
            return inner
        return wrap
    @deco(3)
    def base(x):
        return x * 2
    for i in range(3):
        if i and i:
            return base(a)
    return 0
def f_gen_call_chain(a, xs):
    def g():
        yield from xs
    for i in range(3):
        if i and i:
            return list(g()) + [a]
    return 0
def f_kwargs_deep_host(a, b, c):
    def sink(x, y=0, z=0):
        return x + y + z
    try:
        for i in range(3):
            if i and i:
                return sink(a, y=b, z=c)
    except ValueError:
        return -1
    return 0
def f_call_ternary_arg(a, b, c):
    def sink(x):
        return x + 1
    for i in range(3):
        if i and i:
            return sink(a if b else c)
    return 0
