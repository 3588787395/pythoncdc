# ne09: G9 负对照——浅层 await/yield（预期 MATCH）
async def n_simple_await(src):
    return await src(1)


def n_simple_yield(xs):
    for x in xs:
        yield x


def n_simple_yield_from(xs):
    yield from xs
