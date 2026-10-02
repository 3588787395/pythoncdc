async def aw_return(mgr, v):
    async with mgr:
        return v


async def aw_break(ait, mgr):
    async with mgr:
        async for x in ait:
            if x:
                break
        return x


async def aw_continue(ait, mgr):
    out = 0
    async with mgr:
        async for x in ait:
            if x:
                continue
            out += x
    return out


async def aw_raise(mgr, v):
    async with mgr:
        raise ValueError(v)


async def aw_await_expr(mgr, g):
    async with mgr as f:
        return (await g(f)) + f
