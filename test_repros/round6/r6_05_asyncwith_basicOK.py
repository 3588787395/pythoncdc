# Source Generated with Decompyle++ (Python version)
# File: r6_05_asyncwith_basic.pyc (Python 3.11)

async def aw_single(mgr):
    async with mgr:
        return 1
async def aw_as(mgr):
    async with mgr as f:
        return f
async def aw_two(m1, m2):
    async with m1 as a:
        async with m2 as b:
            return a + b
async def aw_three(m1, m2, m3):
    async with m1 as a:
        async with m2 as b:
            async with m3 as c:
                return a + b + c
async def aw_await_body(mgr, g):
    async with mgr as f:
        return await g(f)
