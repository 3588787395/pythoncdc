# Source Generated with Decompyle++ (Python version)
# File: r6_13_async_await_pos.pyc (Python 3.11)

async def ad_await_binop(g):
    await g(1)
    await g(2)
async def ad_await_subscript(g):
    await g(1)
    return 0
async def ad_await_nested(g, h):
    await g(1)
async def ad_await_compare(g):
    await g(1)
    return 3
async def ad_await_while(g, n):
    while n > 0:
        n -= 1
        await g(n)
    return n
async def ad_await_in_comp(g, xs):
    [await g(x) for x in xs]
