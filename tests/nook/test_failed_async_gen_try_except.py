"""
失败的测试实例: async_gen_try_except
问题: yield await 表达式没有被识别
期望: yield await fetch_item()
实际: await fetch_item() 和 yield None 分开
"""

# 原始测试代码
async def safe_gen():
    try:
        yield await fetch_item()
    except Exception:
        yield None

# 反编译输出（当前有问题的）
DECOMPILED_OUTPUT = '''
async def safe_gen():
    try:
        await fetch_item()
    except Exception:
        yield None
'''

# 期望输出
EXPECTED_OUTPUT = '''
async def safe_gen():
    try:
        yield await fetch_item()
    except Exception:
        yield None
'''
