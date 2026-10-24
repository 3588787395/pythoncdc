# Source Generated with Decompyle++ (Python version)
# File: r6_07_async_five.pyc (Python 3.11)

async def ad_await_chain(g):
    a = await g(1)
    b = await g(2)
    return a + b
async def af_unpack_else(ait):
    result = []
    async for k, v in ait:
        result.append(k + v)
    result.append(-1)
    return result
async def ad_return_await(g):
    return await g(3)
async def ag_yield_await(xs, g):
    for x in xs:
        yield x
    await g(0)
    yield -1
async def ag_af_in_ag(ait):
    async for x in ait:
        yield x
