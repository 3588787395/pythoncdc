"""
第5批：类和对象测试 - 继承和多态
测试单继承、方法重写、多继承的反编译效果
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


# 测试用例1: 单继承
class Base:
    def method(self):
        return 'base'


class Derived(Base):
    pass


def test_single_inheritance():
    obj = Derived()
    return obj.method()


# 测试用例2: 方法重写
class OverridingDerived(Base):
    def method(self):
        return 'derived'


def test_method_override():
    obj = OverridingDerived()
    return obj.method()


# 测试用例3: 调用父类方法
class CallingBaseDerived(Base):
    def method(self):
        base_result = super().method()
        return f'derived calls {base_result}'


def test_call_base_method():
    obj = CallingBaseDerived()
    return obj.method()


# 测试用例4: 多继承
class Mixin1:
    def method1(self):
        return 'mixin1'


class Mixin2:
    def method2(self):
        return 'mixin2'


class MultipleInheritance(Mixin1, Mixin2):
    pass


def test_multiple_inheritance():
    obj = MultipleInheritance()
    return obj.method1(), obj.method2()


# 测试用例5: 菱形继承
class A:
    def method(self):
        return 'A'


class B(A):
    def method(self):
        return 'B'


class C(A):
    def method(self):
        return 'C'


class D(B, C):
    pass


def test_diamond_inheritance():
    obj = D()
    return obj.method()


# 测试用例6: 抽象基类
from abc import ABC, abstractmethod


class AbstractBase(ABC):
    @abstractmethod
    def abstract_method(self):
        pass
    
    def concrete_method(self):
        return 'concrete'


class ConcreteImpl(AbstractBase):
    def abstract_method(self):
        return 'implemented'


def test_abstract_base():
    obj = ConcreteImpl()
    return obj.abstract_method(), obj.concrete_method()


class TestInheritance(unittest.TestCase):
    """测试继承和多态"""
    
    def test_single_inheritance(self):
        """测试单继承"""
        source = '''
class Base:
    def method(self):
        return 'base'

class Derived(Base):
    pass

def test_single_inheritance():
    obj = Derived()
    return obj.method()
'''
        cfg = build_cfg_from_source(source, 'test_single_inheritance')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_method_override(self):
        """测试方法重写"""
        source = '''
class Base:
    def method(self):
        return 'base'

class OverridingDerived(Base):
    def method(self):
        return 'derived'

def test_method_override():
    obj = OverridingDerived()
    return obj.method()
'''
        cfg = build_cfg_from_source(source, 'test_method_override')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_call_base_method(self):
        """测试调用父类方法"""
        source = '''
class Base:
    def method(self):
        return 'base'

class CallingBaseDerived(Base):
    def method(self):
        base_result = super().method()
        return f'derived calls {base_result}'

def test_call_base_method():
    obj = CallingBaseDerived()
    return obj.method()
'''
        cfg = build_cfg_from_source(source, 'test_call_base_method')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiple_inheritance(self):
        """测试多继承"""
        source = '''
class Mixin1:
    def method1(self):
        return 'mixin1'

class Mixin2:
    def method2(self):
        return 'mixin2'

class MultipleInheritance(Mixin1, Mixin2):
    pass

def test_multiple_inheritance():
    obj = MultipleInheritance()
    return obj.method1(), obj.method2()
'''
        cfg = build_cfg_from_source(source, 'test_multiple_inheritance')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_diamond_inheritance(self):
        """测试菱形继承"""
        source = '''
class A:
    def method(self):
        return 'A'

class B(A):
    def method(self):
        return 'B'

class C(A):
    def method(self):
        return 'C'

class D(B, C):
    pass

def test_diamond_inheritance():
    obj = D()
    return obj.method()
'''
        cfg = build_cfg_from_source(source, 'test_diamond_inheritance')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_abstract_base(self):
        """测试抽象基类"""
        source = '''
from abc import ABC, abstractmethod

class AbstractBase(ABC):
    @abstractmethod
    def abstract_method(self):
        pass
    
    def concrete_method(self):
        return 'concrete'

class ConcreteImpl(AbstractBase):
    def abstract_method(self):
        return 'implemented'

def test_abstract_base():
    obj = ConcreteImpl()
    return obj.abstract_method(), obj.concrete_method()
'''
        cfg = build_cfg_from_source(source, 'test_abstract_base')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
