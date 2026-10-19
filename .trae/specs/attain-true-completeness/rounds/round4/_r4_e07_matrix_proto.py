# Source Generated with Decompyle++ (Python version)
# File: e07_matrix.cpython-311.pyc (Python 3.11)

class acm:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *e):
        return False
async def v1(gen):
    return [v async for v in gen]
async def v2(gen):
    r = [v async for v in gen]
    return r
async def v3(gen):
    return [v async for v in gen if v]
async def v4(gen):
    async with acm():
        return [v async for v in gen]
def v5(gen):
    def outer():
        async def inner():
            return [v async for v in gen]
        return inner
    return outer
async def v6(gen):
    return [await g(v) async for v in gen]
async def g(x):
    return x
