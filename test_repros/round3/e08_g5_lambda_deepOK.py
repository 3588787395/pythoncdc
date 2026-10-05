# Source Generated with Decompyle++ (Python version)
# File: e08_g5_lambda_deep.pyc (Python 3.11)

def f_lambda_closure(k):
    fn = lambda x: x + k
    for i in range(3):
        if i and i:
            return fn(i)
    return 0
def f_lambda_default(k):
    fn = lambda x, y=2: x * y + k
    for i in range(3):
        if i and i:
            return fn(i, y=3)
    return 0
def f_lambda_return_factory(k):
    def make():
        return lambda x: x + k
    for i in range(3):
        if i and i:
            return make()(i)
    return 0
def f_lambda_sort_key(pairs):
    for i in range(3):
        if i and i:
            return sorted(pairs, key=lambda p: p[1])
    return 0
def f_lambda_deco_factory(fn):
    def deco(f):
        return lambda : f(*(a), **(k)) + 1
    wrapped = deco(fn)
    for i in range(3):
        if i and i:
            return wrapped(i)
    return 0
def f_lambda_body_ternary(a, b):
    fn = lambda x: x if x > 0 else -x
    for i in range(3):
        if i and i:
            return fn(a) + fn(b)
    return 0
def f_lambda_body_boolop(a, b, d):
    fn = lambda x: x or a
    gn = lambda x: x and b
    for i in range(3):
        if i and i:
            return fn(a) + gn(d)
    return 0
def f_lambda_immediate(a):
    for i in range(3):
        if i and i:
            return (lambda x: x + 1)(a)
    return 0
def f_lambda_in_dict(a):
    ops = {'add': lambda x: x + 1, 'mul': lambda x: x * 2}
    for i in range(3):
        if i and i:
            return ops['add'](a) + ops['mul'](a)
    return 0
def f_lambda_nested(a, b):
    fn = lambda x: lambda y: x + y
    for i in range(3):
        if i and i:
            return fn(a)(b)
    return 0
def f_lambda_default_ternary(a, b):
    fn = lambda x, y=(1 if b else 2): x + y
    for i in range(3):
        if i and i:
            return fn(a)
    return 0
def f_lambda_starargs(a, rest):
    fn = lambda : sum(args) + a
    for i in range(3):
        if i and i:
            return fn(*(rest))
    return 0
