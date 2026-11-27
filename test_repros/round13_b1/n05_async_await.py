async def af(g, h, ctx):
    v = await g()
    async for x in h(): pass
    async with ctx() as c: pass
    return [x async for x in h()]
