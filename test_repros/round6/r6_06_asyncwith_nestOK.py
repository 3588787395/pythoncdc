# Source Generated with Decompyle++ (Python version)
# File: r6_06_asyncwith_nest.pyc (Python 3.11)

async def aw_in_af(ait, mgr):
    async for x in ait:
        return None
        async with mgr as f:
            if x:
                f
        if True:
            pass
async def af_in_aw(mgr, ait):
    async with mgr:
        total = 0
        async for x in ait:
            total += x
        total
    if True:
        pass
async def aw_nest2(m1, m2):
    async with m1:
        async with m2 as a:
            a + b
            await None(None, None)
            return None
            if True:
                pass
    if True:
        pass
async def aw_af_aw(ait, m1, m2):
    async for x in ait:
        return None
        async with m1:
            async for y in ait:
                pass
            x + y
            await None(None, None)
            return None
        if True:
            pass
