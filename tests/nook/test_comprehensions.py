"""
第4批：复杂表达式测试 - 推导式
测试列表/字典/集合推导式的反编译效果
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


class TestListComprehension(unittest.TestCase):
    """测试列表推导式"""
    
    def test_simple_list_comp(self):
        """测试简单列表推导式"""
        source = '''
def test_list_comp():
    return [x**2 for x in range(10)]
'''
        cfg = build_cfg_from_source(source, 'test_list_comp')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_list_comp_with_if(self):
        """测试带条件的列表推导式"""
        source = '''
def test_list_comp_if():
    return [x for x in range(10) if x % 2 == 0]
'''
        cfg = build_cfg_from_source(source, 'test_list_comp_if')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_list_comp(self):
        """测试嵌套列表推导式"""
        source = '''
def test_nested_comp():
    return [[i*j for j in range(3)] for i in range(3)]
'''
        cfg = build_cfg_from_source(source, 'test_nested_comp')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestDictComprehension(unittest.TestCase):
    """测试字典推导式"""
    
    def test_simple_dict_comp(self):
        """测试简单字典推导式"""
        source = '''
def test_dict_comp():
    return {x: x**2 for x in range(5)}
'''
        cfg = build_cfg_from_source(source, 'test_dict_comp')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_dict_comp_with_if(self):
        """测试带条件的字典推导式"""
        source = '''
def test_dict_comp_if():
    return {x: x**2 for x in range(10) if x % 2 == 0}
'''
        cfg = build_cfg_from_source(source, 'test_dict_comp_if')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestSetComprehension(unittest.TestCase):
    """测试集合推导式"""
    
    def test_simple_set_comp(self):
        """测试简单集合推导式"""
        source = '''
def test_set_comp():
    return {x**2 for x in range(10)}
'''
        cfg = build_cfg_from_source(source, 'test_set_comp')
        self.assertIsNotNone(cfg)
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


if __name__ == '__main__':
    unittest.main()
