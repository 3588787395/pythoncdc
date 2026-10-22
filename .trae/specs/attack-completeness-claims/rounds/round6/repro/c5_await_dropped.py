import asyncio


async def inner(x):
    await asyncio.sleep(0)
    return x * 2


async def outer(x):
    y = await inner(x)
    return y


def main():
    try:
        print(asyncio.run(outer(3)))
    except BaseException as e:
        print('EXC', type(e).__name__, e)
