def _host():
    pass

async def outer(fa):
    async with fa() as a:
        y = await fb(a)
    return y
