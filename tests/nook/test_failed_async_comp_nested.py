"""
失败的测试实例: async_comp_nested
问题: 嵌套异步推导式不支持
期望: [y async for x in outer_iter() async for y in inner_iter(x)]
实际: [x async for x in outer_iter()]
"""

# 原始测试代码
async def get_nested():
    return [y async for x in outer_iter() async for y in inner_iter(x)]

# 反编译输出（当前有问题的）
DECOMPILED_OUTPUT = '''
async def get_nested():
    return [x async for x in outer_iter()]()
'''

# 期望输出
EXPECTED_OUTPUT = '''
async def get_nested():
    return [y async for x in outer_iter() async for y in inner_iter(x)]
'''
