# Source Generated with Decompyle++ (Python version)
# File: e12_g9_await_yield.pyc (Python 3.11)

async def f_await_assign_rhs(a, src):
    async with acm9():
        for i in range(3):
            if i:
                v = await src(i)
                return v
    return 0
async def f_await_return(a, src):
    async for i in src(a):
        if i:
            return await src(i)
    return 0
async def f_await_cond_pos(a, src):
    async for i in src(a):
        await src(i)
        if await src(i):
            return i
    return 0
async def f_await_call_arg(a, src):
    def sink(x):
        return x + 1
    async for i in src(a):
        if i:
            return sink(await src(i))
    return 0
async def f_await_deep3(a, src):
    async with acm9():
        async for i in src(a):
            if i:
                return await src(i) + 1
    return 0
async def f_await_boolop(a, src):
    async for i in src(a):
        if await src(i) or a:
            return i
    return 0
def f_yield_expr_arg(xs):
    def sink(x):
        return x
    for i in range(3):
        if i:
            yield sink(yield i)
def f_yield_assign_rhs(xs):
    for i in range(3):
        if i:
            v = yield i
            if v:
                yield v
def f_yield_from_chain(xs):
    def inner():
        yield from xs
    for i in range(3):
        if i:
            yield from inner()
def f_yield_from_deep(xs):
    def lvl2():
        yield from xs
    def lvl1():
        for i in range(2):
            if i:
                yield from lvl2()
    for j in range(2):
        if j:
            yield from lvl1()
def f_yield_in_boolop(xs):
    for i in range(3):
        if i:
            yield yield i or 0
class acm9:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *e):
        return False
