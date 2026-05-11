"""
第6批：装饰器和元类测试 - 函数装饰器
测试简单装饰器、带参数的装饰器、多个装饰器的反编译效果
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


# 测试用例1: 简单装饰器
def simple_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@simple_decorator
def decorated_func():
    return 'decorated'


def test_simple_decorator():
    return decorated_func()


# 测试用例2: 带参数的装饰器
def decorator_with_args(arg):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator


@decorator_with_args('arg')
def decorated_with_args():
    return 'with args'


def test_decorator_with_args():
    return decorated_with_args()


# 测试用例3: 多个装饰器
@simple_decorator
@decorator_with_args('arg')
def multi_decorated():
    return 'multi'


def test_multi_decorator():
    return multi_decorated()


# 测试用例4: 带功能的装饰器（记录日志）
def logging_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper


@logging_decorator
def add(a, b):
    return a + b


def test_logging_decorator():
    return add(1, 2)


# 测试用例5: 装饰器保留元信息
from functools import wraps

def proper_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@proper_decorator
def documented_function():
    """This is a documented function"""
    return 'documented'


def test_proper_decorator():
    return documented_function()


# 测试用例6: 类方法装饰器
class MyClass:
    @simple_decorator
    def decorated_method(self):
        return 'method'


def test_method_decorator():
    obj = MyClass()
    return obj.decorated_method()


class TestDecorators(unittest.TestCase):
    """测试函数装饰器"""
    
    def test_simple_decorator(self):
        """测试简单装饰器"""
        source = '''
def simple_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@simple_decorator
def decorated_func():
    return 'decorated'

def test_simple_decorator():
    return decorated_func()
'''
        cfg = build_cfg_from_source(source, 'test_simple_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_decorator_with_args(self):
        """测试带参数的装饰器"""
        source = '''
def decorator_with_args(arg):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator

@decorator_with_args('arg')
def decorated_with_args():
    return 'with args'

def test_decorator_with_args():
    return decorated_with_args()
'''
        cfg = build_cfg_from_source(source, 'test_decorator_with_args')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multi_decorator(self):
        """测试多个装饰器"""
        source = '''
def simple_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def decorator_with_args(arg):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator

@simple_decorator
@decorator_with_args('arg')
def multi_decorated():
    return 'multi'

def test_multi_decorator():
    return multi_decorated()
'''
        cfg = build_cfg_from_source(source, 'test_multi_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_logging_decorator(self):
        """测试带功能的装饰器"""
        source = '''
def logging_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

@logging_decorator
def add(a, b):
    return a + b

def test_logging_decorator():
    return add(1, 2)
'''
        cfg = build_cfg_from_source(source, 'test_logging_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_proper_decorator(self):
        """测试使用functools.wraps的装饰器"""
        source = '''
from functools import wraps

def proper_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@proper_decorator
def documented_function():
    """This is a documented function"""
    return 'documented'

def test_proper_decorator():
    return documented_function()
'''
        cfg = build_cfg_from_source(source, 'test_proper_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_method_decorator(self):
        """测试类方法装饰器"""
        source = '''
def simple_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class MyClass:
    @simple_decorator
    def decorated_method(self):
        return 'method'

def test_method_decorator():
    obj = MyClass()
    return obj.decorated_method()
'''
        cfg = build_cfg_from_source(source, 'test_method_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
