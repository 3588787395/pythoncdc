# Source Generated with Decompyle++ (Python version)
# File: c4_20_async_five.pyc (Python 3.11)

def sync_gen(n):
    yield n
    yield from range(n)
def e01_await(x):
    async def go():
        return await x
    return go
def e02_async_for(gen):
    async def go():
        async for v in gen:
            yield v
    return go
def e03_async_with(ctx):
    async def go():
        async with ctx as c:
            return c
    return go
def e04_await_deep(x, ys):
    async def go():
        r = 0
        for y in ys:
            if y:
                r = await x + await x
        return r
    return go
def e05_async_compound(gen):
    async def go():
        async for v in gen:
            async with v as c:
                await c
    return go
def e06_async_deep(gen):
    async def go():
        if gen:
            async for v in gen:
                await v
        return 0
    return go
class CAA:
    async def m(self, ctx):
        async with ctx as c:
            return await c
def e07_async_closure(gen):
    def outer():
        async def inner():
            return gen()
        return inner
    return outer
def e08_yield_from(n):
    def go():
        yield from range(n)
        yield from sync_gen(n)
    return go
def e09_async_await_yieldfrom(gen):
    async def go():
        r = 0
        async for v in gen:
            r = await v
        return r
    return go
