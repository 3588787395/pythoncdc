def deco(n):
    def wrap(f):
        return f
    return wrap


@deco(1)
def n_deco(x):
    return x


async def n_await(x):
    return await x


async def n_async_for(gen):
    async for v in gen:
        yield v


async def n_async_with(ctx):
    async with ctx as c:
        return c


def n_yield_from(n):
    yield from range(n)
