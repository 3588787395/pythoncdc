# Source Generated with Decompyle++ (Python version)
# File: r6_15_yield_forms.pyc (Python 3.11)

def make(xs):
    return iter(xs)
def g_yield_from(xs):
    yield from xs
def g_yield_from_call(xs):
    yield from make(xs)
def g_nested_gen(xs):
    for x in xs:
        yield x
def gen_outer(xs):
    yield from g_nested_gen(xs)
def g_mixed(xs, ys):
    yield from xs
    yield 0
    yield from ys
async def ag_yield_only(xs):
    for x in xs:
        yield x
