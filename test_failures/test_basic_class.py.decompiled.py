# Source Generated with Decompyle++ (Python version)
# File: test_basic_class.cpython-311.pyc (Python 3.11)

__doc__ = '\n第5批：类和对象测试 - 基础类定义\n测试简单类、带方法的类、带属性的类的反编译效果\n'
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.cfg import build_cfg, generate_ast
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)
class SimpleClass:
    pass
def test_simple_class():
    return SimpleClass()
class ClassWithMethod:
    def method(self):
        return 'method'
def test_class_method():
    obj = ClassWithMethod()
    return obj.method()
class ClassWithAttr:
    def __init__(self):
        self.attr = 'value'
def test_class_attr():
    obj = ClassWithAttr()
    return obj.attr
class ClassWithClassMethod:
    class_var = 'class_value'
    @classmethod
    def class_method(cls):
        return cls.class_var
def test_classmethod():
    return ClassWithClassMethod.class_method()
class ClassWithStaticMethod:
    @staticmethod
    def static_method():
        return 'static'
def test_staticmethod():
    return ClassWithStaticMethod.static_method()
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
class TestBasicClass:
    __doc__ = '测试基础类定义'
    def test_simple_class(self):
        """测试简单类"""
        source = '\nclass SimpleClass:\n    pass\n\ndef test_simple_class():\n    return SimpleClass()\n'
        cfg = build_cfg_from_source(source, 'test_simple_class')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_class_with_method(self):
        """测试带方法的类"""
        source = "\nclass ClassWithMethod:\n    def method(self):\n        return 'method'\n\ndef test_class_method():\n    obj = ClassWithMethod()\n    return obj.method()\n"
        cfg = build_cfg_from_source(source, 'test_class_method')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_class_with_init(self):
        """测试带__init__的类"""
        source = "\nclass ClassWithAttr:\n    def __init__(self):\n        self.attr = 'value'\n\ndef test_class_attr():\n    obj = ClassWithAttr()\n    return obj.attr\n"
        cfg = build_cfg_from_source(source, 'test_class_attr')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_classmethod(self):
        """测试类方法"""
        source = "\nclass ClassWithClassMethod:\n    class_var = 'class_value'\n    \n    @classmethod\n    def class_method(cls):\n        return cls.class_var\n\ndef test_classmethod():\n    return ClassWithClassMethod.class_method()\n"
        cfg = build_cfg_from_source(source, 'test_classmethod')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_staticmethod(self):
        """测试静态方法"""
        source = "\nclass ClassWithStaticMethod:\n    @staticmethod\n    def static_method():\n        return 'static'\n\ndef test_staticmethod():\n    return ClassWithStaticMethod.static_method()\n"
        cfg = build_cfg_from_source(source, 'test_staticmethod')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_property_decorator(self):
        """测试属性装饰器"""
        source = '\nclass ClassWithProperty:\n    def __init__(self):\n        self._value = 0\n    \n    @property\n    def value(self):\n        return self._value\n    \n    @value.setter\n    def value(self, val):\n        self._value = val\n\ndef test_property():\n    obj = ClassWithProperty()\n    obj.value = 10\n    return obj.value\n'
        cfg = build_cfg_from_source(source, 'test_property')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
if __name__ == '__main__':
    unittest.main()
