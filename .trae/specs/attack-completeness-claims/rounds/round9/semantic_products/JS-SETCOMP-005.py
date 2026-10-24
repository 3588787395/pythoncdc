# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b112b_closure.pyc (Python 3.11)

"""R4 synth: async 推导式闭包交叉变体（B112② 族）。"""
def s_list_closure(gen):
    async def outer():
        items = [v async for v in gen]
        return items
    return outer
def s_set_closure(gen):
    async def outer():
        return {v async for v in gen}
    return outer
def s_deep_closure(gen):
    def mid():
        async def inner():
            return [v async for v in gen if v]
        return inner
    return mid
