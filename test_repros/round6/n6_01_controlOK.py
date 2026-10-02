# Source Generated with Decompyle++ (Python version)
# File: n6_01_control.pyc (Python 3.11)

def c_with_simple(mgr):
    with mgr:
        return 1
def c_with_as(mgr):
    with mgr as f:
        return f
        return None
def c_with_two(m1, m2):
    with m1 as a, m2 as b:
        return (a, b)
        return None
async def c_asyncwith(mgr):
    async with mgr:
        return 2
async def c_asyncfor(ait):
    out = 0
    async for x in ait:
        out += x
    return out
async def c_await(g):
    return await g(1)
async def c_asyncgen(xs):
    for x in xs:
        yield x
