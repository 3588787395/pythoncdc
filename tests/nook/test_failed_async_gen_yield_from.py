"""
失败的测试实例: async_gen_yield_from
问题: yield 5 没有生成
期望: yield 5 在最后
实际: yield 5 缺失
"""

# 原始测试代码
async def combined_gen():
    yield 1
    yield 2
    async for item in sub_gen():
        yield item
    yield 5

# 反编译输出（当前有问题的）
DECOMPILED_OUTPUT = '''
async def combined_gen():
    yield 1
    yield 2
    sub_gen()
    async for item in sub_gen():
        yield item
'''

# 期望输出
EXPECTED_OUTPUT = '''
async def combined_gen():
    yield 1
    yield 2
    async for item in sub_gen():
        yield item
    yield 5
'''
