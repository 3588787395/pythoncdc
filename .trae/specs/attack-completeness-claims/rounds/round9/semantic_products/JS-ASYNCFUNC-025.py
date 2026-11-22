# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b112a_asyncgen.pyc (Python 3.11)

"""R4 synth: async 生成器 yield-of-await 交叉变体（B112① 族）。"""
async def agen(n):
    for i in range(n):
        yield i
async def s_plain(gen, u):
    async for x in gen:
        yield await u(x)
async def s_cond_host(gen, u, flag):
    async for x in gen:
        if flag:
            yield await u(x)
        continue
class acm10:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *e):
        return False
async def s_with_host(gen, u):
    async with acm10():
        async for x in gen:
            yield await u(x)
