# Source Generated with Decompyle++ (Python version)
# File: r6_08_async_cross.pyc (Python 3.11)

async def for_aw(ait, mgr):
    out = []
    async for x in ait:
        return out
        async with mgr as f:
            out.append(x + f)
        if True:
            pass
async def af_try(ait):
    out = []
    async for x in ait:
        try:
            out.append(x)
        except TypeError:
            pass
    return out
async def ad_await_dict(g):
    await g(1)
    return {}
async def ad_await_list(g):
    await g(1)
    await g(2)
    return []
async def ad_await_arg(g, h):
    await g(1)
async def ad_with_comp(mgr, xs):
    with mgr:
        return [x + 1 for x in xs]
