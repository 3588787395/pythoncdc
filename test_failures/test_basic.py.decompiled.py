__doc__ = """
CFG基础功能测试
测试基本代码结构的CFG构建
"""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.cfg import build_cfg, generate_ast
def build_cfg_from_source(source, func_name=None):
    code_obj = compile(source, '<string>', 'exec')
    return build_cfg(code_obj)
class TestBasicFunction(unittest.TestCase):
    __doc__ = '测试基本函数定义'
    def test_simple_function(self):
        """测试简单函数"""
        source = """
def test():
    return 42
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_function_with_args(self):
        """测试带参数的函数"""
        source = """
def test(a, b, c=None):
    return a + b + (c or 0)
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    def test_function_with_locals(self):
        """测试带局部变量的函数"""
        source = """
def test():
    x = 1
    y = 2
    z = x + y
    return z
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
class TestVariableAssignment(unittest.TestCase):
    __doc__ = '测试变量赋值'
    def test_simple_assignment(self):
        """测试简单赋值"""
        source = """
def test():
    x = 10
    return x
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    def test_multiple_assignment(self):
        """测试多重赋值"""
        source = """
def test():
    a, b, c = 1, 2, 3
    return a + b + c
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    def test_chained_assignment(self):
        """测试链式赋值"""
        source = """
def test():
    x = y = z = 0
    return x + y + z
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
class TestArithmeticOperations(unittest.TestCase):
    __doc__ = '测试算术运算'
    def test_basic_arithmetic(self):
        """测试基本算术运算"""
        source = """
def test():
    a = 10 + 5
    b = 10 - 5
    c = 10 * 5
    d = 10 / 5
    return a + b + c + d
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    def test_complex_expression(self):
        """测试复杂表达式"""
        source = """
def test():
    result = (10 + 5) * 2 - 3 / 2
    return result
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
class TestReturnValues(unittest.TestCase):
    __doc__ = '测试返回值'
    def test_simple_return(self):
        """测试简单返回"""
        source = """
def test():
    return 42
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    def test_return_expression(self):
        """测试返回表达式"""
        source = """
def test():
    return 10 + 20 * 2
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    def test_return_variable(self):
        """测试返回变量"""
        source = """
def test():
    x = 100
    return x
"""
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
if __name__ == '__main__':
    unittest.main()
