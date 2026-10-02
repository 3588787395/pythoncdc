# Source Generated with Decompyle++ (Python version)
# File: r5_10_comp_async.pyc (Python 3.11)

async def a_async_for(ait):
    return [x async for x in ait]
async def a_async_cond(ait):
    return [x async for x in ait if x > 0]
async def a_async_multi(ait, b):
    await ait()
async def a_async_set(ait):
    return {x async for x in ait}
async def a_async_dict(ait):
    return {x: x * 2 async for x in ait}
async def a_await_body(ait, g):
    await ait()
