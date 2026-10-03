# Source Generated with Decompyle++ (Python version)
# File: r6_06_asyncwith_nest.pyc (Python 3.11)

async def aw_in_af(ait, mgr):
    async for x in ait:
        async with mgr as f:
            if x:
                return f
async def af_in_aw(mgr, ait):
    async with mgr:
        total = 0
        async for x in ait:
            total += x
        return total
async def aw_nest2(m1, m2):
    async with m1 as a:
        async with m2 as b:
            return a + b
async def aw_af_aw(ait, m1, m2):
    async for x in ait:
        async with m1:
            async for y in ait:
                return x + y
