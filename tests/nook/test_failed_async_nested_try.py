"""
失败的测试实例: async_nested_try
问题: 嵌套 try-except 结构混乱
期望: 内部 except InnerError 和外部 except OuterError 都正确
实际: 内部 try-except 被错误地合并到外部 else 块中
"""

# 原始测试代码
async def nested_handling():
    try:
        outer = await outer_op()
        try:
            inner = await inner_op(outer)
            return inner
        except InnerError as e:
            await handle_inner(e)
    except OuterError as e:
        await handle_outer(e)

# 反编译输出（当前有问题的）
DECOMPILED_OUTPUT = '''
async def nested_handling():
    try:
        await outer_op()
    except OuterError as e:
        await handle_outer(e)
    else:
        await inner_op(outer)
        return inner
        None
        await handle_inner(e)
        e = None
        return None
    e = None
    e = None
'''

# 期望输出
EXPECTED_OUTPUT = '''
async def nested_handling():
    try:
        outer = await outer_op()
        try:
            inner = await inner_op(outer)
            return inner
        except InnerError as e:
            await handle_inner(e)
    except OuterError as e:
        await handle_outer(e)
'''
