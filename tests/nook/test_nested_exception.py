"""
第2批：异常处理测试 - 嵌套异常处理
测试嵌套try/异常在finally中抛出的反编译效果
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


class TestNestedTry(unittest.TestCase):
    """测试嵌套try"""
    
    def test_nested_try_except(self):
        """测试嵌套try-except"""
        source = '''
def test_nested_try():
    try:
        try:
            result = 1 / 0
        except ValueError:
            result = 'inner error'
    except ZeroDivisionError:
        result = 'outer error'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_nested_try')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_try_different_exceptions(self):
        """测试嵌套try捕获不同异常"""
        source = '''
def test_nested_different():
    try:
        try:
            raise ValueError('inner')
        except ValueError:
            result = 'caught inner'
    except TypeError:
        result = 'caught outer'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_nested_different')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_deeply_nested_try(self):
        """测试深度嵌套try"""
        source = '''
def test_deeply_nested():
    try:
        try:
            try:
                result = 1 / 0
            except TypeError:
                result = 'level 3'
        except ValueError:
            result = 'level 2'
    except ZeroDivisionError:
        result = 'level 1'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_deeply_nested')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestExceptionInFinally(unittest.TestCase):
    """测试异常在finally中抛出"""
    
    def test_exception_in_finally(self):
        """测试finally中抛出异常"""
        source = '''
def test_exception_in_finally():
    try:
        return 'try'
    finally:
        raise RuntimeError('finally error')
'''
        cfg = build_cfg_from_source(source, 'test_exception_in_finally')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_exception_in_finally_with_except(self):
        """测试finally中抛出异常且外部有except"""
        source = '''
def test_exception_in_finally_with_except():
    try:
        try:
            return 'try'
        finally:
            raise RuntimeError('finally error')
    except RuntimeError:
        return 'caught'
'''
        cfg = build_cfg_from_source(source, 'test_exception_in_finally_with_except')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestTryExceptInLoop(unittest.TestCase):
    """测试循环中的异常处理"""
    
    def test_except_in_for_loop(self):
        """测试for循环中的异常处理"""
        source = '''
def test_except_in_for():
    results = []
    for i in range(5):
        try:
            if i == 2:
                raise ValueError('error')
            results.append(i)
        except ValueError:
            results.append('error')
    return results
'''
        cfg = build_cfg_from_source(source, 'test_except_in_for')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_in_while_loop(self):
        """测试while循环中的异常处理"""
        source = '''
def test_except_in_while():
    count = 0
    results = []
    while count < 5:
        try:
            if count == 2:
                raise ValueError('error')
            results.append(count)
        except ValueError:
            results.append('error')
        count += 1
    return results
'''
        cfg = build_cfg_from_source(source, 'test_except_in_while')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_break_in_except(self):
        """测试except中的break"""
        source = '''
def test_break_in_except():
    for i in range(10):
        try:
            if i == 5:
                raise ValueError('stop')
        except ValueError:
            break
    return i
'''
        cfg = build_cfg_from_source(source, 'test_break_in_except')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_continue_in_except(self):
        """测试except中的continue"""
        source = '''
def test_continue_in_except():
    results = []
    for i in range(5):
        try:
            if i % 2 == 0:
                raise ValueError('skip')
            results.append(i)
        except ValueError:
            continue
    return results
'''
        cfg = build_cfg_from_source(source, 'test_continue_in_except')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestNestedExceptionDecompilation(unittest.TestCase):
    """测试嵌套异常处理反编译"""
    
    def test_nested_try_decompile(self):
        """测试嵌套try反编译"""
        source = '''
def test_nested_try():
    try:
        try:
            result = 1 / 0
        except ValueError:
            result = 'inner'
    except ZeroDivisionError:
        result = 'outer'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_nested_try')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_exception_in_finally_decompile(self):
        """测试finally中异常反编译"""
        source = '''
def test_exception_in_finally():
    try:
        return 'try'
    finally:
        raise RuntimeError('error')
'''
        cfg = build_cfg_from_source(source, 'test_exception_in_finally')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
