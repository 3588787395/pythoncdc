"""
第6批：装饰器和元类测试 - 类装饰器
测试简单类装饰器、带方法的类装饰器的反编译效果
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


# 测试用例1: 简单类装饰器
def class_decorator(cls):
    class Wrapped(cls):
        pass
    return Wrapped


@class_decorator
class DecoratedClass:
    pass


def test_class_decorator():
    return DecoratedClass()


# 测试用例2: 带方法的类装饰器
def add_method_decorator(cls):
    cls.added_method = lambda self: 'added'
    return cls


@add_method_decorator
class ClassWithAddedMethod:
    pass


def test_add_method():
    obj = ClassWithAddedMethod()
    return obj.added_method()


# 测试用例3: 添加属性的类装饰器
def add_property_decorator(cls):
    cls.class_name = cls.__name__
    return cls


@add_property_decorator
class ClassWithAddedProperty:
    def __init__(self):
        self.instance_var = 'instance'


def test_add_property():
    obj = ClassWithAddedProperty()
    return obj.class_name, obj.instance_var


# 测试用例4: 带参数的装饰器
def parameterized_decorator(prefix):
    def decorator(cls):
        cls.prefix = prefix
        return cls
    return decorator


@parameterized_decorator('TEST')
class ParameterizedClass:
    pass


def test_parameterized_decorator():
    return ParameterizedClass.prefix


# 测试用例5: 多个类装饰器
@add_property_decorator
@add_method_decorator
class MultiDecoratedClass:
    def original_method(self):
        return 'original'


def test_multi_class_decorator():
    obj = MultiDecoratedClass()
    return obj.original_method()


# 测试用例6: 类装饰器带功能
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


@singleton
class SingletonClass:
    def __init__(self):
        self.value = 'singleton'


def test_singleton_decorator():
    obj1 = SingletonClass()
    obj2 = SingletonClass()
    return obj1 is obj2


class TestClassDecorators(unittest.TestCase):
    """测试类装饰器"""
    
    def test_class_decorator(self):
        """测试简单类装饰器"""
        source = '''
def class_decorator(cls):
    class Wrapped(cls):
        pass
    return Wrapped

@class_decorator
class DecoratedClass:
    pass

def test_class_decorator():
    return DecoratedClass()
'''
        cfg = build_cfg_from_source(source, 'test_class_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_add_method_decorator(self):
        """测试添加方法的类装饰器"""
        source = '''
def add_method_decorator(cls):
    cls.added_method = lambda self: 'added'
    return cls

@add_method_decorator
class ClassWithAddedMethod:
    pass

def test_add_method():
    obj = ClassWithAddedMethod()
    return obj.added_method()
'''
        cfg = build_cfg_from_source(source, 'test_add_method')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_add_property_decorator(self):
        """测试添加属性的类装饰器"""
        source = '''
def add_property_decorator(cls):
    cls.class_name = cls.__name__
    return cls

@add_property_decorator
class ClassWithAddedProperty:
    def __init__(self):
        self.instance_var = 'instance'

def test_add_property():
    obj = ClassWithAddedProperty()
    return obj.class_name, obj.instance_var
'''
        cfg = build_cfg_from_source(source, 'test_add_property')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_parameterized_decorator(self):
        """测试带参数的类装饰器"""
        source = '''
def parameterized_decorator(prefix):
    def decorator(cls):
        cls.prefix = prefix
        return cls
    return decorator

@parameterized_decorator('TEST')
class ParameterizedClass:
    pass

def test_parameterized_decorator():
    return ParameterizedClass.prefix
'''
        cfg = build_cfg_from_source(source, 'test_parameterized_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multi_class_decorator(self):
        """测试多个类装饰器"""
        source = '''
def add_method_decorator(cls):
    cls.added_method = lambda self: 'added'
    return cls

def add_property_decorator(cls):
    cls.class_name = cls.__name__
    return cls

@add_property_decorator
@add_method_decorator
class MultiDecoratedClass:
    def original_method(self):
        return 'original'

def test_multi_class_decorator():
    obj = MultiDecoratedClass()
    return obj.original_method()
'''
        cfg = build_cfg_from_source(source, 'test_multi_class_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_singleton_decorator(self):
        """测试单例装饰器"""
        source = '''
def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class SingletonClass:
    def __init__(self):
        self.value = 'singleton'

def test_singleton_decorator():
    obj1 = SingletonClass()
    obj2 = SingletonClass()
    return obj1 is obj2
'''
        cfg = build_cfg_from_source(source, 'test_singleton_decorator')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
