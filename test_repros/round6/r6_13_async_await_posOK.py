# Source Generated with Decompyle++ (Python version)
# File: r6_13_async_await_pos.pyc (Python 3.11)

async def ad_await_binop(g):
    return await g(1) + await g(2)
async def ad_await_subscript(g):
    return (await g(1))[0]
async def ad_await_nested(g, h):
    return h(await g(await g(1)))
async def ad_await_compare(g):
    return await g(1) > 3
async def ad_await_while(g, n):
    while n > 0:
        n -= 1
        await g(n)
    return n
async def ad_await_in_comp(g, xs):
    return [await g(x) for x in xs]
