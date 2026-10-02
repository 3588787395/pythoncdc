"""Round5 复核变体探针：B23（async 推导式组合）修复的变体攻击。"""


async def g(x):
    return x * 10


async def a3_mixed(ait, b, c2):
    """三 clause 混排：async + sync + async。"""
    return [x + y + z async for x in ait for y in b async for z in c2]


async def a_genexp(ait):
    """async GenExp（括号形式）。"""
    return sum(x async for x in ait)


async def a_dict_comp(ait, b):
    """async dict comp 双 clause。"""
    return {x: y async for x in ait for y in b}


async def a_await_set(ait):
    """async set comp，elt 含 await 调用。"""
    return {await g(x) async for x in ait}
