"""
第1批：基础控制流测试 - 循环结构
测试for/while/嵌套循环的反编译效果
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


class TestForLoop(unittest.TestCase):
    """测试for循环"""
    
    def test_simple_for(self):
        """测试简单for循环"""
        source = '''
def test_simple_for(n):
    total = 0
    for i in range(n):
        total += i
    return total
'''
        cfg = build_cfg_from_source(source, 'test_simple_for')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_for_with_list(self):
        """测试遍历列表的for循环"""
        source = '''
def test_for_with_list(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
'''
        cfg = build_cfg_from_source(source, 'test_for_with_list')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_for_with_dict(self):
        """测试遍历字典的for循环"""
        source = '''
def test_for_with_dict(data):
    result = []
    for key, value in data.items():
        result.append((key, value))
    return result
'''
        cfg = build_cfg_from_source(source, 'test_for_with_dict')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_for(self):
        """测试嵌套for循环"""
        source = '''
def test_nested_loop():
    result = []
    for i in range(3):
        for j in range(3):
            result.append((i, j))
    return result
'''
        cfg = build_cfg_from_source(source, 'test_nested_loop')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestWhileLoop(unittest.TestCase):
    """测试while循环"""
    
    def test_simple_while(self):
        """测试简单while循环"""
        source = '''
def test_simple_while(n):
    count = 0
    while count < n:
        count += 1
    return count
'''
        cfg = build_cfg_from_source(source, 'test_simple_while')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_while_with_condition(self):
        """测试带复杂条件的while循环"""
        source = '''
def test_while_with_condition(x, y):
    count = 0
    while x > 0 and y > 0:
        x -= 1
        y -= 1
        count += 1
    return count
'''
        cfg = build_cfg_from_source(source, 'test_while_with_condition')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_while_true(self):
        """测试while True循环"""
        source = '''
def test_while_true(n):
    count = 0
    while True:
        if count >= n:
            break
        count += 1
    return count
'''
        cfg = build_cfg_from_source(source, 'test_while_true')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestLoopDecompilation(unittest.TestCase):
    """测试循环反编译结果验证"""
    
    def test_for_decompile_basic(self):
        """测试基本for循环反编译"""
        source = '''
def test_for_basic(n):
    total = 0
    for i in range(n):
        total += i
    return total
'''
        cfg = build_cfg_from_source(source, 'test_for_basic')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_while_decompile_basic(self):
        """测试基本while循环反编译"""
        source = '''
def test_while_basic(n):
    count = 0
    while count < n:
        count += 1
    return count
'''
        cfg = build_cfg_from_source(source, 'test_while_basic')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
