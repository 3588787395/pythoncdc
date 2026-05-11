"""
失败的测试实例: async_for_target
问题: 复杂循环变量不支持
期望: async for [a, b, c] in async_lists()
实际: async for a, b, c in async_lists()
"""

# 原始测试代码
async def unpack_items():
    async for key, value in async_items():
        store(key, value)
    
    async for [a, b, c] in async_lists():
        process(a, b, c)

# 反编译输出（当前有问题的）
DECOMPILED_OUTPUT = '''
async def unpack_items():
    async_items()
    async for key, value in async_items():
        store(key, value)
    async for a, b, c in async_lists():
        process(a, b, c)
'''

# 期望输出
EXPECTED_OUTPUT = '''
async def unpack_items():
    async for key, value in async_items():
        store(key, value)
    async for [a, b, c] in async_lists():
        process(a, b, c)
'''
