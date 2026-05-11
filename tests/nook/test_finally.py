"""
第2批：异常处理测试 - finally子句
测试try-finally/try-except-finally的反编译效果
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


class TestSimpleFinally(unittest.TestCase):
    """测试简单try-finally"""
    
    def test_simple_finally(self):
        """测试简单try-finally"""
        source = '''
def test_simple_finally():
    try:
        result = 1 / 0
    finally:
        cleanup = True
    return result
'''
        cfg = build_cfg_from_source(source, 'test_simple_finally')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_finally_no_exception(self):
        """测试无异常时的finally执行"""
        source = '''
def test_finally_no_exception():
    result = None
    try:
        x = 10
    finally:
        result = 'finally executed'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_finally_no_exception')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_finally_with_exception(self):
        """测试有异常时的finally执行"""
        source = '''
def test_finally_with_exception():
    result = None
    try:
        x = 1 / 0
    finally:
        result = 'finally executed'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_finally_with_exception')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestExceptFinally(unittest.TestCase):
    """测试try-except-finally"""
    
    def test_except_finally(self):
        """测试try-except-finally"""
        source = '''
def test_except_finally():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 'error'
    finally:
        cleanup = True
    return result
'''
        cfg = build_cfg_from_source(source, 'test_except_finally')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_finally_no_exception(self):
        """测试无异常时的except-finally"""
        source = '''
def test_except_finally_no_exception():
    try:
        result = 10 / 2
    except ZeroDivisionError:
        result = 'error'
    finally:
        cleanup = True
    return result
'''
        cfg = build_cfg_from_source(source, 'test_except_finally_no_exception')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiple_except_finally(self):
        """测试多个except子句加finally"""
        source = '''
def test_multiple_except_finally(x):
    try:
        if x == 1:
            raise ValueError('value')
        elif x == 2:
            raise TypeError('type')
    except ValueError:
        result = 'value error'
    except TypeError:
        result = 'type error'
    finally:
        cleanup = True
    return result
'''
        cfg = build_cfg_from_source(source, 'test_multiple_except_finally')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestFinallyReturn(unittest.TestCase):
    """测试finally中的return"""
    
    def test_finally_return(self):
        """测试finally中的return覆盖"""
        source = '''
def test_finally_return():
    try:
        return 'try'
    finally:
        return 'finally'
'''
        cfg = build_cfg_from_source(source, 'test_finally_return')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_finally_return_with_exception(self):
        """测试异常时finally中的return"""
        source = '''
def test_finally_return_with_exception():
    try:
        raise ValueError('error')
    except:
        return 'except'
    finally:
        return 'finally'
'''
        cfg = build_cfg_from_source(source, 'test_finally_return_with_exception')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestFinallyDecompilation(unittest.TestCase):
    """测试finally反编译"""
    
    def test_simple_finally_decompile(self):
        """测试简单finally反编译"""
        source = '''
def test_simple_finally():
    try:
        result = 1 / 0
    finally:
        cleanup = True
    return result
'''
        cfg = build_cfg_from_source(source, 'test_simple_finally')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_except_finally_decompile(self):
        """测试except-finally反编译"""
        source = '''
def test_except_finally():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 'error'
    finally:
        cleanup = True
    return result
'''
        cfg = build_cfg_from_source(source, 'test_except_finally')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
