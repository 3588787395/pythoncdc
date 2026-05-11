"""
第2批：异常处理测试 - 基础异常处理
测试try-except/try-except-else的反编译效果
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


class TestSimpleExcept(unittest.TestCase):
    """测试简单try-except"""
    
    def test_simple_except(self):
        """测试简单try-except"""
        source = '''
def test_simple_except():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 'error'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_simple_except')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_with_message(self):
        """测试带异常消息的except"""
        source = '''
def test_except_with_message():
    try:
        raise ValueError('test error')
    except ValueError as e:
        return str(e)
'''
        cfg = build_cfg_from_source(source, 'test_except_with_message')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiple_except(self):
        """测试多个except子句"""
        source = '''
def test_multiple_except(x):
    try:
        if x == 1:
            raise ValueError('value error')
        elif x == 2:
            raise TypeError('type error')
        elif x == 3:
            raise RuntimeError('runtime error')
    except ValueError:
        return 'value'
    except TypeError:
        return 'type'
    except RuntimeError:
        return 'runtime'
    return 'ok'
'''
        cfg = build_cfg_from_source(source, 'test_multiple_except')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_tuple(self):
        """测试元组形式的except"""
        source = '''
def test_except_tuple():
    try:
        raise ValueError('test')
    except (ValueError, TypeError):
        return 'caught'
    return 'ok'
'''
        cfg = build_cfg_from_source(source, 'test_except_tuple')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_bare_except(self):
        """测试裸except"""
        source = '''
def test_bare_except():
    try:
        result = 1 / 0
    except:
        result = 'any error'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_bare_except')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestExceptElse(unittest.TestCase):
    """测试try-except-else"""
    
    def test_except_else(self):
        """测试try-except-else"""
        source = '''
def test_except_else():
    try:
        result = 10 / 2
    except ZeroDivisionError:
        result = 'error'
    else:
        result = 'success'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_except_else')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_else_no_exception(self):
        """测试无异常时的else执行"""
        source = '''
def test_except_else_no_exception():
    try:
        x = 10
    except:
        x = 'error'
    else:
        x = 'no error'
    return x
'''
        cfg = build_cfg_from_source(source, 'test_except_else_no_exception')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_else_with_exception(self):
        """测试有异常时的else不执行"""
        source = '''
def test_except_else_with_exception():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        x = 'caught'
    else:
        x = 'not executed'
    return x
'''
        cfg = build_cfg_from_source(source, 'test_except_else_with_exception')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestExceptAs(unittest.TestCase):
    """测试except as语法"""
    
    def test_except_as(self):
        """测试except as"""
        source = '''
def test_except_as():
    try:
        raise ValueError('test message')
    except ValueError as e:
        return e.args[0]
'''
        cfg = build_cfg_from_source(source, 'test_except_as')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_except_as_multiple(self):
        """测试多个except as"""
        source = '''
def test_except_as_multiple(x):
    try:
        if x == 1:
            raise ValueError('value')
        else:
            raise TypeError('type')
    except ValueError as ve:
        return str(ve)
    except TypeError as te:
        return str(te)
'''
        cfg = build_cfg_from_source(source, 'test_except_as_multiple')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestBasicExceptionDecompilation(unittest.TestCase):
    """测试基础异常处理反编译"""
    
    def test_simple_except_decompile(self):
        """测试简单except反编译"""
        source = '''
def test_simple_except():
    try:
        result = 1 / 0
    except ZeroDivisionError:
        result = 'error'
    return result
'''
        cfg = build_cfg_from_source(source, 'test_simple_except')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_multiple_except_decompile(self):
        """测试多个except反编译"""
        source = '''
def test_multiple_except(x):
    try:
        if x == 1:
            raise ValueError('value')
    except ValueError:
        return 'value'
    except TypeError:
        return 'type'
    return 'ok'
'''
        cfg = build_cfg_from_source(source, 'test_multiple_except')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
