# e12d: e12 拆分补测——6 个 await 单元（发射文本合法，取单元读数）
async def f_await_assign_rhs(a, src):
    async with acm9():
        for i in range(3):
            if i:
                v = await src(i)
                return v
    return 0


async def f_await_return(a, src):
    async for i in src(a):
        if i:
            return await src(i)
    return 0


async def f_await_cond_pos(a, src):
    async for i in src(a):
        if await src(i):
            return i
    return 0


async def f_await_call_arg(a, src):
    def sink(x):
        return x + 1
    async for i in src(a):
        if i:
            return sink(await src(i))
    return 0


async def f_await_deep3(a, src):
    async with acm9():
        async for i in src(a):
            if i:
                return (await src(i)) + 1
    return 0


async def f_await_boolop(a, src):
    async for i in src(a):
        if (await src(i)) or a:
            return i
    return 0


class acm9:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *e):
        return False
