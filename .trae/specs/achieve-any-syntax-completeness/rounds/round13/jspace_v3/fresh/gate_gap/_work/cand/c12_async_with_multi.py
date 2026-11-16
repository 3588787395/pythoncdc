def _host():
    pass

async def outer(fa, fb, fc):
    async with fa() as a, fb() as b:
        s = await a
        t = await b
    return s, t
