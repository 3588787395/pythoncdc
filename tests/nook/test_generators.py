"""
第7批：生成器和协程测试 - 生成器函数
测试简单生成器、带条件的生成器、生成器表达式的反编译效果
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


# 测试用例1: 简单生成器
def simple_generator():
    yield 1
    yield 2
    yield 3


def test_simple_generator():
    return list(simple_generator())


# 测试用例2: 带参数的生成器
def param_generator(n):
    for i in range(n):
        yield i


def test_param_generator():
    return list(param_generator(5))


# 测试用例3: 带条件的生成器
def conditional_generator(n):
    for i in range(n):
        if i % 2 == 0:
            yield i


def test_conditional_generator():
    return list(conditional_generator(10))


# 测试用例4: 生成器表达式
def test_generator_expression():
    return list(x**2 for x in range(10))


# 测试用例5: 嵌套生成器
def nested_generator():
    for i in range(3):
        for j in range(3):
            yield (i, j)


def test_nested_generator():
    return list(nested_generator())


# 测试用例6: yield from
def sub_generator():
    yield 1
    yield 2


def yield_from_generator():
    yield from sub_generator()
    yield 3


def test_yield_from():
    return list(yield_from_generator())


# 测试用例7: 带return的生成器
def generator_with_return(n):
    for i in range(n):
        yield i
    return 'done'


def test_generator_with_return():
    gen = generator_with_return(3)
    result = list(gen)
    return result


class TestGenerators(unittest.TestCase):
    """测试生成器函数"""
    
    def test_simple_generator(self):
        """测试简单生成器"""
        source = '''
def simple_generator():
    yield 1
    yield 2
    yield 3

def test_simple_generator():
    return list(simple_generator())
'''
        cfg = build_cfg_from_source(source, 'test_simple_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_param_generator(self):
        """测试带参数的生成器"""
        source = '''
def param_generator(n):
    for i in range(n):
        yield i

def test_param_generator():
    return list(param_generator(5))
'''
        cfg = build_cfg_from_source(source, 'test_param_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_conditional_generator(self):
        """测试带条件的生成器"""
        source = '''
def conditional_generator(n):
    for i in range(n):
        if i % 2 == 0:
            yield i

def test_conditional_generator():
    return list(conditional_generator(10))
'''
        cfg = build_cfg_from_source(source, 'test_conditional_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_generator_expression(self):
        """测试生成器表达式"""
        source = '''
def test_generator_expression():
    return list(x**2 for x in range(10))
'''
        cfg = build_cfg_from_source(source, 'test_generator_expression')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_generator(self):
        """测试嵌套生成器"""
        source = '''
def nested_generator():
    for i in range(3):
        for j in range(3):
            yield (i, j)

def test_nested_generator():
    return list(nested_generator())
'''
        cfg = build_cfg_from_source(source, 'test_nested_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_yield_from(self):
        """测试yield from"""
        source = '''
def sub_generator():
    yield 1
    yield 2

def yield_from_generator():
    yield from sub_generator()
    yield 3

def test_yield_from():
    return list(yield_from_generator())
'''
        cfg = build_cfg_from_source(source, 'test_yield_from')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_generator_with_return(self):
        """测试带return的生成器"""
        source = '''
def generator_with_return(n):
    for i in range(n):
        yield i
    return 'done'

def test_generator_with_return():
    gen = generator_with_return(3)
    result = list(gen)
    return result
'''
        cfg = build_cfg_from_source(source, 'test_generator_with_return')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
