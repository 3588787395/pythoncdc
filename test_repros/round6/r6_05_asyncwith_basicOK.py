# Source Generated with Decompyle++ (Python version)
# File: r6_05_asyncwith_basic.pyc (Python 3.11)

async def aw_single(mgr):
    async with mgr:
    return 1
async def aw_as(mgr):
    async with mgr as f:
        f
    if True:
        pass
async def aw_two(m1, m2):
    async with m1:
        async with m2 as a:
            a + b
            await None(None, None)
            return None
            if True:
                pass
    if True:
        pass
async def aw_three(m1, m2, m3):
    a + b + c
    await None(None, None)
    await None(None, None)
    await None(None, None)
async def aw_await_body(mgr, g):
    async with mgr as f:
        await g(f)
    if True:
        pass
