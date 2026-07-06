# Source Generated with Decompyle++ (Python version)
# File: test_async.cpython-311.pyc (Python 3.11)

__doc__ = '\n第7批：生成器和协程测试 - 异步特性\n测试简单协程、async for、async with的反编译效果\n'
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.cfg import build_cfg, generate_ast
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)
async def simple_coroutine():
    return 'coroutine'
def test_simple_coroutine():
    import asyncio
    return asyncio.run(simple_coroutine())
async def async_generator():
    for i in range(3):
        yield i
async def use_async_for():
    result = []
    async for i in async_generator():
        result.append(i)
    else:
        return result
def test_async_for():
    import asyncio
    return asyncio.run(use_async_for())
class AsyncContext:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
async def use_async_with():
    async with AsyncContext() as ctx:
        pass
    return 'inside'
def test_async_with():
    import asyncio
    return asyncio.run(use_async_with())
async def async_add(a, b):
    return a + b
async def use_await():
    result = await async_add(1, 2)
    return result
def test_await():
    import asyncio
    return asyncio.run(use_await())
async def async_range(n):
    for i in range(n):
        yield i
async def use_async_generator():
    result = []
    async for i in async_range(5):
        result.append(i)
    else:
        return result
def test_async_generator():
    import asyncio
    return asyncio.run(use_async_generator())
async def async_comprehension():
    return [x async for x in async_generator()]
def test_async_comprehension():
    import asyncio
    return asyncio.run(async_comprehension())
class TestAsync:
    __doc__ = '测试异步特性'
    def test_simple_coroutine(self):
        """测试简单协程"""
        source = "\nasync def simple_coroutine():\n    return 'coroutine'\n\ndef test_simple_coroutine():\n    import asyncio\n    return asyncio.run(simple_coroutine())\n"
        cfg = build_cfg_from_source(source, 'test_simple_coroutine')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_async_for(self):
        """测试async for"""
        source = '\nasync def async_generator():\n    for i in range(3):\n        yield i\n\nasync def use_async_for():\n    result = []\n    async for i in async_generator():\n        result.append(i)\n    return result\n\ndef test_async_for():\n    import asyncio\n    return asyncio.run(use_async_for())\n'
        cfg = build_cfg_from_source(source, 'test_async_for')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_async_with(self):
        """测试async with"""
        source = "\nclass AsyncContext:\n    async def __aenter__(self):\n        return self\n    \n    async def __aexit__(self, exc_type, exc_val, exc_tb):\n        pass\n\nasync def use_async_with():\n    async with AsyncContext() as ctx:\n        return 'inside'\n\ndef test_async_with():\n    import asyncio\n    return asyncio.run(use_async_with())\n"
        cfg = build_cfg_from_source(source, 'test_async_with')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_await(self):
        """测试await表达式"""
        source = '\nasync def async_add(a, b):\n    return a + b\n\nasync def use_await():\n    result = await async_add(1, 2)\n    return result\n\ndef test_await():\n    import asyncio\n    return asyncio.run(use_await())\n'
        cfg = build_cfg_from_source(source, 'test_await')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_async_generator(self):
        """测试异步生成器"""
        source = '\nasync def async_range(n):\n    for i in range(n):\n        yield i\n\nasync def use_async_generator():\n    result = []\n    async for i in async_range(5):\n        result.append(i)\n    return result\n\ndef test_async_generator():\n    import asyncio\n    return asyncio.run(use_async_generator())\n'
        cfg = build_cfg_from_source(source, 'test_async_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_async_comprehension(self):
        """测试异步推导式"""
        source = '\nasync def async_generator():\n    for i in range(3):\n        yield i\n\nasync def async_comprehension():\n    return [x async for x in async_generator()]\n\ndef test_async_comprehension():\n    import asyncio\n    return asyncio.run(async_comprehension())\n'
        cfg = build_cfg_from_source(source, 'test_async_comprehension')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
if __name__ == '__main__':
    unittest.main()
