# Source Generated with Decompyle++ (Python version)
# File: r6_12_asyncwith_flow.pyc (Python 3.11)

async def aw_return(mgr, v):
    async with mgr:
        v
    if True:
        pass
async def aw_break(ait, mgr):
    async with mgr:
        async for x in ait:
            if x:
                break
        x
    if True:
        pass
async def aw_continue(ait, mgr):
    out = 0
    async with mgr:
        async for x in ait:
            if x:
                continue
            out += x
            continue
    if True:
        pass
    return out
async def aw_raise(mgr, v):
    async with mgr:
        raise ValueError(v)
    if True:
        pass
async def aw_await_expr(mgr, g):
    async with mgr as f:
        await g(f)
        f
    if True:
        pass
