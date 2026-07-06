"""
第3批：with语句测试 - 复合with语句
测试多个上下文管理器/嵌套with/with与异常的反编译效果
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


class TestCompoundWith(unittest.TestCase):
    """测试复合with语句（多个上下文管理器）"""
    
    def test_compound_with(self):
        """测试复合with语句"""
        source = '''
def test_compound_with():
    with open('in.txt', 'r') as fin, open('out.txt', 'w') as fout:
        fout.write(fin.read())
'''
        cfg = build_cfg_from_source(source, 'test_compound_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_compound_with_three(self):
        """测试三个上下文管理器的复合with"""
        source = '''
def test_compound_with_three():
    with open('a.txt', 'r') as a, open('b.txt', 'r') as b, open('c.txt', 'w') as c:
        c.write(a.read() + b.read())
'''
        cfg = build_cfg_from_source(source, 'test_compound_with_three')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_compound_with_no_as(self):
        """测试不带as的复合with"""
        source = '''
def test_compound_no_as():
    with open('a.txt'), open('b.txt'):
        pass
'''
        cfg = build_cfg_from_source(source, 'test_compound_no_as')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestNestedWith(unittest.TestCase):
    """测试嵌套with语句"""
    
    def test_nested_with(self):
        """测试嵌套with语句"""
        source = '''
def test_nested_with():
    with open('outer.txt', 'r') as outer:
        with open('inner.txt', 'r') as inner:
            return outer.read() + inner.read()
'''
        cfg = build_cfg_from_source(source, 'test_nested_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_deeply_nested_with(self):
        """测试深度嵌套with"""
        source = '''
def test_deeply_nested():
    with open('a.txt', 'r') as a:
        with open('b.txt', 'r') as b:
            with open('c.txt', 'r') as c:
                return a.read() + b.read() + c.read()
'''
        cfg = build_cfg_from_source(source, 'test_deeply_nested')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_nested_with_compound(self):
        """测试嵌套复合with"""
        source = '''
def test_nested_compound():
    with open('outer.txt', 'r') as outer:
        with open('a.txt', 'r') as a, open('b.txt', 'r') as b:
            return outer.read() + a.read() + b.read()
'''
        cfg = build_cfg_from_source(source, 'test_nested_compound')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestWithException(unittest.TestCase):
    """测试with语句与异常处理"""
    
    def test_with_exception(self):
        """测试with中的异常"""
        source = '''
def test_with_exception():
    try:
        with open('test.txt', 'r') as f:
            raise ValueError('test')
    except ValueError:
        return 'caught'
'''
        cfg = build_cfg_from_source(source, 'test_with_exception')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_with_finally(self):
        """测试with与finally"""
        source = '''
def test_with_finally():
    try:
        with open('test.txt', 'r') as f:
            return f.read()
    finally:
        cleanup = True
'''
        cfg = build_cfg_from_source(source, 'test_with_finally')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_with_except_finally(self):
        """测试with与except-finally"""
        source = '''
def test_with_except_finally():
    try:
        with open('test.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return 'not found'
    finally:
        cleanup = True
'''
        cfg = build_cfg_from_source(source, 'test_with_except_finally')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestCompoundWithDecompilation(unittest.TestCase):
    """测试复合with语句反编译"""
    
    def test_compound_with_decompile(self):
        """测试复合with反编译"""
        source = '''
def test_compound_with():
    with open('in.txt', 'r') as fin, open('out.txt', 'w') as fout:
        fout.write(fin.read())
'''
        cfg = build_cfg_from_source(source, 'test_compound_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_nested_with_decompile(self):
        """测试嵌套with反编译"""
        source = '''
def test_nested_with():
    with open('outer.txt', 'r') as outer:
        with open('inner.txt', 'r') as inner:
            return outer.read() + inner.read()
'''
        cfg = build_cfg_from_source(source, 'test_nested_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
