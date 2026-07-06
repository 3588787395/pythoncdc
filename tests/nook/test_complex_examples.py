"""
第8批：综合测试和优化 - 复杂示例
测试复杂控制流组合、复杂类结构、装饰器组合的反编译效果
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


# 测试用例1: 复杂控制流组合
def complex_control_flow(data):
    result = []
    for item in data:
        if isinstance(item, int):
            if item > 0:
                result.append(item * 2)
            elif item < 0:
                result.append(abs(item))
            else:
                continue
        elif isinstance(item, str):
            try:
                num = int(item)
                result.append(num)
            except ValueError:
                result.append(0)
    return result


def test_complex_control_flow():
    return complex_control_flow([1, -2, 0, '3', 'abc'])


# 测试用例2: 复杂类结构
class ComplexClass:
    class_var = 'class'
    
    def __init__(self, value):
        self.value = value
        self._private = 'private'
    
    @property
    def prop(self):
        return self._private
    
    @prop.setter
    def prop(self, value):
        self._private = value
    
    @classmethod
    def class_method(cls):
        return cls.class_var
    
    @staticmethod
    def static_method():
        return 'static'


def test_complex_class():
    obj = ComplexClass(10)
    return obj.prop, obj.class_method(), obj.static_method()


# 测试用例3: 复杂装饰器组合
def decorator1(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def decorator2(arg):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator


@decorator1
@decorator2('arg')
class DecoratedClass:
    @decorator1
    def method(self):
        return 'method'


def test_complex_decorator():
    obj = DecoratedClass()
    return obj.method()


# 测试用例4: 嵌套函数和闭包
def outer_function(x):
    def inner_function(y):
        def deepest_function(z):
            return x + y + z
        return deepest_function
    return inner_function


def test_nested_functions():
    return outer_function(1)(2)(3)


# 测试用例5: 复杂异常处理
def complex_exception_handling():
    results = []
    try:
        try:
            result = 1 / 0
        except ZeroDivisionError:
            results.append('inner caught')
            raise
    except ZeroDivisionError:
        results.append('outer caught')
    finally:
        results.append('finally')
    return results


def test_complex_exception():
    return complex_exception_handling()


# 测试用例6: 复杂生成器组合
def complex_generator():
    for i in range(5):
        if i % 2 == 0:
            yield i
        else:
            yield from sub_generator(i)


def sub_generator(n):
    for i in range(n):
        yield i * 10


def test_complex_generator():
    return list(complex_generator())


class TestComplexExamples(unittest.TestCase):
    """测试复杂示例"""
    
    def test_complex_control_flow(self):
        """测试复杂控制流组合"""
        source = '''
def complex_control_flow(data):
    result = []
    for item in data:
        if isinstance(item, int):
            if item > 0:
                result.append(item * 2)
            elif item < 0:
                result.append(abs(item))
            else:
                continue
        elif isinstance(item, str):
            try:
                num = int(item)
                result.append(num)
            except ValueError:
                result.append(0)
    return result

def test_complex_control_flow():
    return complex_control_flow([1, -2, 0, '3', 'abc'])
'''
        cfg = build_cfg_from_source(source, 'test_complex_control_flow')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_complex_class(self):
        """测试复杂类结构"""
        source = '''
class ComplexClass:
    class_var = 'class'
    
    def __init__(self, value):
        self.value = value
        self._private = 'private'
    
    @property
    def prop(self):
        return self._private
    
    @prop.setter
    def prop(self, value):
        self._private = value
    
    @classmethod
    def class_method(cls):
        return cls.class_var
    
    @staticmethod
    def static_method():
        return 'static'

def test_complex_class():
    obj = ComplexClass(10)
    return obj.prop, obj.class_method(), obj.static_method()
'''
        cfg = build_cfg_from_source(source, 'test_complex_class')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_complex_decorator(self):
        """测试复杂装饰器组合"""
        source = '''
def decorator1(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def decorator2(arg):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return actual_decorator

@decorator1
@decorator2('arg')
class DecoratedClass:
    @decorator1
    def method(self):
        return 'method'

def test_complex_decorator():
    obj = DecoratedClass()
    return obj.method()
'''
        cfg = build_cfg_from_source(source, 'test_complex_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_functions(self):
        """测试嵌套函数和闭包"""
        source = '''
def outer_function(x):
    def inner_function(y):
        def deepest_function(z):
            return x + y + z
        return deepest_function
    return inner_function

def test_nested_functions():
    return outer_function(1)(2)(3)
'''
        cfg = build_cfg_from_source(source, 'test_nested_functions')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_complex_exception(self):
        """测试复杂异常处理"""
        source = '''
def complex_exception_handling():
    results = []
    try:
        try:
            result = 1 / 0
        except ZeroDivisionError:
            results.append('inner caught')
            raise
    except ZeroDivisionError:
        results.append('outer caught')
    finally:
        results.append('finally')
    return results

def test_complex_exception():
    return complex_exception_handling()
'''
        cfg = build_cfg_from_source(source, 'test_complex_exception')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_complex_generator(self):
        """测试复杂生成器组合"""
        source = '''
def complex_generator():
    for i in range(5):
        if i % 2 == 0:
            yield i
        else:
            yield from sub_generator(i)

def sub_generator(n):
    for i in range(n):
        yield i * 10

def test_complex_generator():
    return list(complex_generator())
'''
        cfg = build_cfg_from_source(source, 'test_complex_generator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
