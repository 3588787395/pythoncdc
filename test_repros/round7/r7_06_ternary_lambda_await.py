"""R7-06 lambda 体与 await 右侧三元位置面。"""


def t_lambda_ternary(flag):
    f = lambda x: x if flag else -x
    return f(3)


def t_lambda_ternary_two_args(flag):
    g = lambda a, b: a if flag else b
    return g(1, 2)


def t_lambda_in_arg_ternary(xs, flag):
    return list(map(lambda v: v if flag else 0, xs))


async def t_await_ternary_branches(io, flag):
    return await io.a() if flag else await io.b()


async def t_await_assign_ternary(io, b, flag):
    x = await io.a() if flag else b
    return x


async def t_await_deep_ternary(io, flag, n):
    r = (await io.a()) if flag else (await io.b()) + n
    return r
