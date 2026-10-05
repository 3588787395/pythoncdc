# Source Generated with Decompyle++ (Python version)
# File: e09b_g6_async_comps.pyc (Python 3.11)

async def a_one(ait, xs):
    async for i in ait():
        if i:
            return [await g2(x) for x in xs if x]
    return []
async def a_two(ait, xs):
    async with acm():
        return [x async for x in ait()]
    return []
async def a_three(ait, d):
    acc = []
    async for i in ait():
        if i:
            acc.extend(await ({k: await g2(v) for k, v in d.items() if v}))
    return acc
async def a_four(ait, xs):
    async for i in ait():
        if i:
            return sum((await g2(x) for x in xs))
    return 0
class acm:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *e):
        return False
async def g2(x):
    return x
