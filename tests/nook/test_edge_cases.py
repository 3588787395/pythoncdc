"""
第8批：综合测试和优化 - 边界情况
测试空函数、只有pass的循环、复杂嵌套、超长表达式、大量局部变量
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


# 测试用例1: 空函数
def empty_function():
    pass


def test_empty_function():
    return empty_function()


# 测试用例2: 只有pass的循环
def pass_only_loop():
    for i in range(10):
        pass


def test_pass_only_loop():
    return pass_only_loop()


# 测试用例3: 复杂嵌套
def deeply_nested():
    if True:
        if True:
            if True:
                if True:
                    return 'deep'


def test_deeply_nested():
    return deeply_nested()


# 测试用例4: 超长表达式
def long_expression():
    return (1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 +
            11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20)


def test_long_expression():
    return long_expression()


# 测试用例5: 大量局部变量
def many_locals():
    a1 = a2 = a3 = a4 = a5 = 1
    b1 = b2 = b3 = b4 = b5 = 2
    c1 = c2 = c3 = c4 = c5 = 3
    return a1 + b1 + c1


def test_many_locals():
    return many_locals()


# 测试用例6: 多行字符串
def multiline_string():
    text = """
    This is a multiline
    string with multiple
    lines of text.
    """
    return text


def test_multiline_string():
    return multiline_string()


# 测试用例7: 复杂列表推导式
def complex_list_comp():
    return [[i*j for j in range(5)] for i in range(5)]


def test_complex_list_comp():
    return complex_list_comp()


# 测试用例8: 多重条件表达式
def multiple_ternary(x, y, z):
    return 'all' if x > 0 and y > 0 and z > 0 else 'some' if x > 0 or y > 0 or z > 0 else 'none'


def test_multiple_ternary():
    return multiple_ternary(1, 0, -1)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_empty_function(self):
        """测试空函数"""
        source = '''
def empty_function():
    pass

def test_empty_function():
    return empty_function()
'''
        cfg = build_cfg_from_source(source, 'test_empty_function')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_pass_only_loop(self):
        """测试只有pass的循环"""
        source = '''
def pass_only_loop():
    for i in range(10):
        pass

def test_pass_only_loop():
    return pass_only_loop()
'''
        cfg = build_cfg_from_source(source, 'test_pass_only_loop')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_deeply_nested(self):
        """测试复杂嵌套"""
        source = '''
def deeply_nested():
    if True:
        if True:
            if True:
                if True:
                    return 'deep'

def test_deeply_nested():
    return deeply_nested()
'''
        cfg = build_cfg_from_source(source, 'test_deeply_nested')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_long_expression(self):
        """测试超长表达式"""
        source = '''
def long_expression():
    return (1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9 + 10 +
            11 + 12 + 13 + 14 + 15 + 16 + 17 + 18 + 19 + 20)

def test_long_expression():
    return long_expression()
'''
        cfg = build_cfg_from_source(source, 'test_long_expression')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_many_locals(self):
        """测试大量局部变量"""
        source = '''
def many_locals():
    a1 = a2 = a3 = a4 = a5 = 1
    b1 = b2 = b3 = b4 = b5 = 2
    c1 = c2 = c3 = c4 = c5 = 3
    return a1 + b1 + c1

def test_many_locals():
    return many_locals()
'''
        cfg = build_cfg_from_source(source, 'test_many_locals')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiline_string(self):
        """测试多行字符串"""
        source = '''
def multiline_string():
    text = """
    This is a multiline
    string with multiple
    lines of text.
    """
    return text

def test_multiline_string():
    return multiline_string()
'''
        cfg = build_cfg_from_source(source, 'test_multiline_string')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_complex_list_comp(self):
        """测试复杂列表推导式"""
        source = '''
def complex_list_comp():
    return [[i*j for j in range(5)] for i in range(5)]

def test_complex_list_comp():
    return complex_list_comp()
'''
        cfg = build_cfg_from_source(source, 'test_complex_list_comp')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiple_ternary(self):
        """测试多重条件表达式"""
        source = '''
def multiple_ternary(x, y, z):
    return 'all' if x > 0 and y > 0 and z > 0 else 'some' if x > 0 or y > 0 or z > 0 else 'none'

def test_multiple_ternary():
    return multiple_ternary(1, 0, -1)
'''
        cfg = build_cfg_from_source(source, 'test_multiple_ternary')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
