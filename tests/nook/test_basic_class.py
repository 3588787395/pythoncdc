"""
第5批：类和对象测试 - 基础类定义
测试简单类、带方法的类、带属性的类的反编译效果
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


# 测试用例1: 简单类
class SimpleClass:
    pass


def test_simple_class():
    return SimpleClass()


# 测试用例2: 带方法的类
class ClassWithMethod:
    def method(self):
        return 'method'


def test_class_method():
    obj = ClassWithMethod()
    return obj.method()


# 测试用例3: 带属性的类
class ClassWithAttr:
    def __init__(self):
        self.attr = 'value'


def test_class_attr():
    obj = ClassWithAttr()
    return obj.attr


# 测试用例4: 类方法
class ClassWithClassMethod:
    class_var = 'class_value'
    
    @classmethod
    def class_method(cls):
        return cls.class_var


def test_classmethod():
    return ClassWithClassMethod.class_method()


# 测试用例5: 静态方法
class ClassWithStaticMethod:
    @staticmethod
    def static_method():
        return 'static'


def test_staticmethod():
    return ClassWithStaticMethod.static_method()


# 测试用例6: 属性装饰器
class ClassWithProperty:
    def __init__(self):
        self._value = 0
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val


def test_property():
    obj = ClassWithProperty()
    obj.value = 10
    return obj.value


class TestBasicClass(unittest.TestCase):
    """测试基础类定义"""
    
    def test_simple_class(self):
        """测试简单类"""
        source = '''
class SimpleClass:
    pass

def test_simple_class():
    return SimpleClass()
'''
        cfg = build_cfg_from_source(source, 'test_simple_class')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_class_with_method(self):
        """测试带方法的类"""
        source = '''
class ClassWithMethod:
    def method(self):
        return 'method'

def test_class_method():
    obj = ClassWithMethod()
    return obj.method()
'''
        cfg = build_cfg_from_source(source, 'test_class_method')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_class_with_init(self):
        """测试带__init__的类"""
        source = '''
class ClassWithAttr:
    def __init__(self):
        self.attr = 'value'

def test_class_attr():
    obj = ClassWithAttr()
    return obj.attr
'''
        cfg = build_cfg_from_source(source, 'test_class_attr')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_classmethod(self):
        """测试类方法"""
        source = '''
class ClassWithClassMethod:
    class_var = 'class_value'
    
    @classmethod
    def class_method(cls):
        return cls.class_var

def test_classmethod():
    return ClassWithClassMethod.class_method()
'''
        cfg = build_cfg_from_source(source, 'test_classmethod')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_staticmethod(self):
        """测试静态方法"""
        source = '''
class ClassWithStaticMethod:
    @staticmethod
    def static_method():
        return 'static'

def test_staticmethod():
    return ClassWithStaticMethod.static_method()
'''
        cfg = build_cfg_from_source(source, 'test_staticmethod')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_property_decorator(self):
        """测试属性装饰器"""
        source = '''
class ClassWithProperty:
    def __init__(self):
        self._value = 0
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val

def test_property():
    obj = ClassWithProperty()
    obj.value = 10
    return obj.value
'''
        cfg = build_cfg_from_source(source, 'test_property')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
