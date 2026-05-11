"""
第1批：基础控制流测试 - 简单条件语句
测试if/if-else/if-elif-else的反编译效果
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


class TestSimpleIf(unittest.TestCase):
    """测试简单if语句"""
    
    def test_simple_if(self):
        """测试简单if"""
        source = '''
def test_simple_if(x):
    if x > 0:
        return 'positive'
    return 'non-positive'
'''
        cfg = build_cfg_from_source(source, 'test_simple_if')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_if_else(self):
        """测试if-else"""
        source = '''
def test_if_else(x):
    if x > 0:
        result = 'positive'
    else:
        result = 'non-positive'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_if_else')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_if_elif_else(self):
        """测试if-elif-else链"""
        source = '''
def test_if_elif_else(x):
    if x > 10:
        result = 'greater than 10'
    elif x == 10:
        result = 'equal to 10'
    else:
        result = 'less than 10'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_if_elif_else')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiple_conditions(self):
        """测试多条件判断"""
        source = '''
def test_multiple_conditions(x, y):
    if x > 0 and y > 0:
        return 'both positive'
    elif x > 0 or y > 0:
        return 'one positive'
    else:
        return 'none positive'
'''
        cfg = build_cfg_from_source(source, 'test_multiple_conditions')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_if(self):
        """测试嵌套if"""
        source = '''
def test_nested_if(x, y):
    if x > 0:
        if y > 0:
            return 'both positive'
        else:
            return 'x positive, y not'
    return 'x not positive'
'''
        cfg = build_cfg_from_source(source, 'test_nested_if')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestIfDecompilation(unittest.TestCase):
    """测试if语句反编译结果验证"""
    
    def test_if_decompile_basic(self):
        """测试基本if反编译"""
        source = '''
def test_if_basic(x):
    if x > 0:
        return True
    return False
'''
        # 编译
        code = compile(source, '<string>', 'exec')
        
        # 反编译测试（这里应该调用实际的反编译器）
        cfg = build_cfg_from_source(source, 'test_if_basic')
        self.assertIsNotNone(cfg)
        
        # 验证CFG结构
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_if_else_decompile(self):
        """测试if-else反编译"""
        source = '''
def test_if_else(x):
    if x > 0:
        result = 'positive'
    else:
        result = 'negative'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_if_else')
        self.assertIsNotNone(cfg)
        
        # 应该有两个分支（if和else）
        # 这里可以进一步验证CFG的分支结构


if __name__ == '__main__':
    unittest.main()
