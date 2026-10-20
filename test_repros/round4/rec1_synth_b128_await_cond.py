"""R4 synth: if 条件位形 await 链交叉变体（B128 族）。"""


async def s_if(io, i):
    if await io.a(i):
        return i
    return 0


async def s_else(io, i):
    if i:
        return 0
    elif await io.a(i):
        return i
    return 1


async def s_expr_ctx(io, i):
    v = await io.a(i) if i else 0
    return v
