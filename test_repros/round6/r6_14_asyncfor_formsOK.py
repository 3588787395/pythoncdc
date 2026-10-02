# Source Generated with Decompyle++ (Python version)
# File: r6_14_asyncfor_forms.pyc (Python 3.11)

async def af_break_continue(ait):
    out = []
    async for x in ait:
        if x < 0:
            continue
        elif x > 9:
            break
        else:
            out.append(x)
            continue
    return out
async def af_unpack(ait):
    out = 0
    async for a, b in ait:
        out += a * b
    return out
async def af_else(ait):
    out = 0
    async for x in ait:
        out += x
    out += 100
    return out
async def af_nested(ait1, ait2):
    out = 0
    async for x in ait1:
        async for y in ait2:
            out += x * y
    return out
async def af_return_body(ait):
    async for x in ait:
        if x > 5:
            return x
async def af_star(ait):
    out = 0
    async for a, *rest in ait:
        out += a + rest[0]
    return out
