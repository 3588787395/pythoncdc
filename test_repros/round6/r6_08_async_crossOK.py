# Source Generated with Decompyle++ (Python version)
# File: r6_08_async_cross.pyc (Python 3.11)

async def for_aw(ait, mgr):
    out = []
    async for x in ait:
        async with mgr as f:
            out.append(x + f)
    return out
async def af_try(ait):
    out = []
    async for x in ait:
        try:
            out.append(x)
        except TypeError:
            break
    return out
async def ad_await_dict(g):
    return {'k': await g(1)}
async def ad_await_list(g):
    return [await g(1), await g(2)]
async def ad_await_arg(g, h):
    return h(await g(await g(1)))
async def ad_with_comp(mgr, xs):
    with mgr:
        return [x + 1 for x in xs]
