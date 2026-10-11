# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b96_async_battery.pyc (Python 3.11)

async def b1(ait, d):
    acc = []
    async for i in ait():
        if i:
            acc.extend({k: await g(v) for k, v in d.items() if v})
    return acc
async def b2(xs):
    return [await h(x) for x in xs if x]
async def b3(xs):
    return xs()
async def b4(xs):
    return sum((1 for x in xs if await h(x)))
async def b5(xs):
    return {await h(x) for x in xs}
async def b6(d):
    return {k: await h(v) for k, v in d.items()}
async def b7(xs):
    async def inner():
        return xs()
    return inner
async def g(x):
    return x
async def h(x):
    return x
