"""r3_29: for 迭代变量元组解包 / starred 目标；async for-else。"""


def tuple_unpack(items):
    out = []
    for a, b in items:
        if a > b:
            break
        out.append((a, b))
    else:
        out.append("ok")
    return out


def starred_target(items):
    out = []
    for head, *tail in items:
        if not tail:
            continue
        out.append((head, tail))
    else:
        out.append("done")
    return out


def nested_unpack(items):
    out = []
    for (a, b), c in items:
        if c == 0:
            break
        out.append(a + b + c)
    else:
        out.append(-1)
    return out


async def afor_with_else(src):
    out = []
    async for v in src:
        if v is None:
            break
        out.append(v)
    else:
        out.append("aelse")
    return out
