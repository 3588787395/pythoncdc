# e09b: async 推导式（B96 已封闭面回归）——await in comprehension / async for comp
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
            acc.extend({k: await g2(v) for k, v in d.items() if v})
    return acc


async def a_four(ait, xs):
    async for i in ait():
        if i:
            return sum(1 for x in xs if await g2(x))
    return 0


class acm:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *e):
        return False


async def g2(x):
    return x
