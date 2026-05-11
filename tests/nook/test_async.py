"""
第7批：生成器和协程测试 - 异步特性
测试简单协程、async for、async with的反编译效果
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.cfg import build_cfg, generate_ast

# 为了保持兼容性，添加build_cfg_from_source别名
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)


# 测试用例1: 简单协程
async def simple_coroutine():
    return 'coroutine'


def test_simple_coroutine():
    import asyncio
    return asyncio.run(simple_coroutine())


# 测试用例2: async for
async def async_generator():
    for i in range(3):
        yield i


async def use_async_for():
    result = []
    async for i in async_generator():
        result.append(i)
    return result


def test_async_for():
    import asyncio
    return asyncio.run(use_async_for())


# 测试用例3: async with
class AsyncContext:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def use_async_with():
    async with AsyncContext() as ctx:
        return 'inside'


def test_async_with():
    import asyncio
    return asyncio.run(use_async_with())


# 测试用例4: await表达式
async def async_add(a, b):
    return a + b


async def use_await():
    result = await async_add(1, 2)
    return result


def test_await():
    import asyncio
    return asyncio.run(use_await())


# 测试用例5: 异步生成器
async def async_range(n):
    for i in range(n):
        yield i


async def use_async_generator():
    result = []
    async for i in async_range(5):
        result.append(i)
    return result


def test_async_generator():
    import asyncio
    return asyncio.run(use_async_generator())


# 测试用例6: 异步推导式
async def async_comprehension():
    return [x async for x in async_generator()]


def test_async_comprehension():
    import asyncio
    return asyncio.run(async_comprehension())


class TestAsync(unittest.TestCase):
    """测试异步特性"""
    
    def test_simple_coroutine(self):
        """测试简单协程"""
        source = '''
async def simple_coroutine():
    return 'coroutine'

def test_simple_coroutine():
    import asyncio
    return asyncio.run(simple_coroutine())
'''
        cfg = build_cfg_from_source(source, 'test_simple_coroutine')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_async_for(self):
        """测试async for"""
        source = '''
async def async_generator():
    for i in range(3):
        yield i

async def use_async_for():
    result = []
    async for i in async_generator():
        result.append(i)
    return result

def test_async_for():
    import asyncio
    return asyncio.run(use_async_for())
'''
        cfg = build_cfg_from_source(source, 'test_async_for')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_async_with(self):
        """测试async with"""
        source = '''
class AsyncContext:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

async def use_async_with():
    async with AsyncContext() as ctx:
        return 'inside'

def test_async_with():
    import asyncio
    return asyncio.run(use_async_with())
'''
        cfg = build_cfg_from_source(source, 'test_async_with')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_await(self):
        """测试await表达式"""
        source = '''
async def async_add(a, b):
    return a + b

async def use_await():
    result = await async_add(1, 2)
    return result

def test_await():
    import asyncio
    return asyncio.run(use_await())
'''
        cfg = build_cfg_from_source(source, 'test_await')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_async_generator(self):
        """测试异步生成器"""
        source = '''
async def async_range(n):
    for i in range(n):
        yield i

async def use_async_generator():
    result = []
    async for i in async_range(5):
        result.append(i)
    return result

def test_async_generator():
    import asyncio
    return asyncio.run(use_async_generator())
'''
        cfg = build_cfg_from_source(source, 'test_async_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_async_comprehension(self):
        """测试异步推导式"""
        source = '''
async def async_generator():
    for i in range(3):
        yield i

async def async_comprehension():
    return [x async for x in async_generator()]

def test_async_comprehension():
    import asyncio
    return asyncio.run(async_comprehension())
'''
        cfg = build_cfg_from_source(source, 'test_async_comprehension')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
