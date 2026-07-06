"""
L1函数与类定义测试用例 (12项)

覆盖Python函数和类定义中的控制流结构：
- FN01-FN04: 函数定义（4项）
- FN05-FN06: 装饰器（2项）
- CL01-CL04: 类定义（4项）
- CL05-CL06: 类装饰器和方法（2项）
"""

import ast
from .base import ControlFlowTestCase


# ============================================================================
# FN01-FN04: 函数定义（4项）
# ============================================================================

class TestFN01SimpleFunction(ControlFlowTestCase):
    """FN01: 简单函数定义"""
    SOURCE_CODE = """def add(x, y):
    return x + y"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")
        self.assertEqual(func_def.name, 'add', "函数名应为add")


class TestFN02DefaultArgs(ControlFlowTestCase):
    """FN02: 带默认参数的函数"""
    SOURCE_CODE = """def greet(name, greeting='Hello'):
    return f'{greeting}, {name}'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")
        self.assertGreaterEqual(len(func_def.args.defaults), 1, "应该包含默认参数")


class TestFN03NestedFunction(ControlFlowTestCase):
    """FN03: 嵌套函数（闭包）"""
    SOURCE_CODE = """def outer(x):
    def inner(y):
        return x + y
    return inner(10)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_count = len(self.find_all_nodes(tree, ast.FunctionDef))
        self.assertEqual(func_count, 2, "应该有2个嵌套的函数定义")


class TestFN04StarArgs(ControlFlowTestCase):
    """FN04: *args和**kwargs"""
    SOURCE_CODE = """def func_with_args(a, *args, **kwargs):
    return (a, list(args), kwargs)"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")
        self.assertIsNotNone(func_def.args.vararg, "应该有*args")
        self.assertIsNotNone(func_def.args.kwarg, "应该有**kwargs")


# ============================================================================
# FN05-FN06: 装饰器（2项）
# ============================================================================

class TestFN05DecoratedFunction(ControlFlowTestCase):
    """FN05: 装饰器函数"""
    SOURCE_CODE = """def decorator(func):
    def wrapper(*args, **kwargs):
        print('before')
        result = func(*args, **kwargs)
        print('after')
        return result
    return wrapper

@decorator
def target_function(x):
    return x * 2"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_count = len(self.find_all_nodes(tree, ast.FunctionDef))
        self.assertGreaterEqual(func_count, 3, "应该包含至少3个函数定义")


class TestFN06ChainedDecorators(ControlFlowTestCase):
    """FN06: 链式装饰器"""
    SOURCE_CODE = """@decorator_a
@decorator_b
def target(x):
    return x * 2"""

    def test_structure_correct(self):
        # Cat-D: decorator chain reconstruction requires stack tracing + cross-block scanning — not yet implemented
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含函数定义")
        self.assertEqual(len(func_def.decorator_list), 2, "应该有2个装饰器")


# ============================================================================
# CL01-CL04: 类定义（4项）
# ============================================================================

class TestCL01SimpleClass(ControlFlowTestCase):
    """CL01: 简单类定义"""
    SOURCE_CODE = """class MyClass:
    pass"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        class_def = self.find_node(tree, ast.ClassDef)
        self.assertIsNotNone(class_def, "应该包含类定义")


class TestCL02ClassWithAttributes(ControlFlowTestCase):
    """CL02: 带属性的类"""
    SOURCE_CODE = """class Person:
    species = 'human'
    
    def __init__(self, name, age):
        self.name = name
        self.age = age"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        class_def = self.find_node(tree, ast.ClassDef)
        self.assertIsNotNone(class_def, "应该包含类定义")
        func_def = self.find_node(tree, ast.FunctionDef)
        self.assertIsNotNone(func_def, "应该包含__init__方法")


class TestCL03ClassWithMethods(ControlFlowTestCase):
    """CL03: 带多个方法的类"""
    SOURCE_CODE = """class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
        return self.result
    
    def sub(self, x):
        self.result -= x
        return self.result
    
    def reset(self):
        self.result = 0"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        class_def = self.find_node(tree, ast.ClassDef)
        self.assertIsNotNone(class_def, "应该包含类定义")
        func_count = len(self.find_all_nodes(tree, ast.FunctionDef))
        self.assertGreaterEqual(func_count, 4, "应该包含至少4个方法")


class TestCL04ClassInheritance(ControlFlowTestCase):
    """CL04: 类继承"""
    SOURCE_CODE = """class Base:
    def base_method(self):
        return 'base'

class Derived(Base):
    def derived_method(self):
        return 'derived'"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        class_count = len(self.find_all_nodes(tree, ast.ClassDef))
        self.assertEqual(class_count, 2, "应该有2个类定义")


# ============================================================================
# CL05-CL06: 类装饰器和方法（2项）
# ============================================================================

class TestCL05DecoratedClass(ControlFlowTestCase):
    """CL05: 带装饰器的类"""
    SOURCE_CODE = """@dataclass
class Point:
    x: int
    y: int"""

    def test_structure_correct(self):
        # Cat-D: class decorator reconstruction requires stack tracing + cross-block scanning — not yet implemented
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        class_def = self.find_node(tree, ast.ClassDef)
        self.assertIsNotNone(class_def, "应该包含类定义")
        self.assertEqual(len(class_def.decorator_list), 1, "应该有1个装饰器")


class TestCL06StaticAndClassMethod(ControlFlowTestCase):
    """CL06: 静态方法和类方法"""
    SOURCE_CODE = """class Utility:
    @staticmethod
    def static_add(x, y):
        return x + y
    
    @classmethod
    def class_create(cls, data):
        instance = cls()
        instance.data = data
        return instance"""

    def test_structure_correct(self):
        decompiled = self.decompile()
        tree = self.verify_syntax(decompiled)
        self.assertIsNotNone(tree)
        func_count = len(self.find_all_nodes(tree, ast.FunctionDef))
        self.assertEqual(func_count, 2, "应该有2个方法定义")


# 测试统计：总计12项
# FN01-FN04: 4项函数定义
# FN05-FN06: 2项装饰器
# CL01-CL04: 4项类定义
# CL05-CL06: 2项类装饰器和方法
