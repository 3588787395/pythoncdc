"""R8-09 Deep host combos: for-else+del+raise / try-finally return / while chained assign / with assert / match del-assign-raise / async / comprehension assert."""


def r8_dh_for_else_del(xs):
    for i, v in enumerate(xs):
        if v is None:
            del xs[i]
            break
    else:
        raise ValueError("no None")
    return xs


def r8_dh_try_finally_return(n):
    try:
        if n > 0:
            return "pos"
        raise ValueError("neg")
    finally:
        n = n


def r8_dh_while_assign_chain(xs):
    out = {}
    i = 0
    while i < len(xs):
        out[i] = out["last"] = xs[i]
        i += 1
    return out


def r8_dh_with_assert(path):
    with open(path) as fh:
        data = fh.read()
        assert data, "empty file"
    return data


def r8_dh_match_multi(x):
    match x:
        case {"op": op, **rest}:
            if "tmp" in rest:
                del rest["tmp"]
            return op, rest
        case [a, b]:
            a, b = b, a
            return a, b
        case _:
            assert x is not None
            raise TypeError("bad shape")


async def r8_dh_async_raise(agen, lim):
    total = 0
    async for v in agen:
        if v > lim:
            raise OverflowError("too big")
        total += v
    return total


def r8_dh_comprehension_assert(xs):
    keep = lambda v: v % 2 == 0
    ys = [x for x in xs if keep(x)]
    assert len(ys) <= len(xs), "filter invariant"
    return ys
