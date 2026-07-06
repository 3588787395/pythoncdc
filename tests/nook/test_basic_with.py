"""
第3批：with语句测试 - 基础with语句
测试简单with/多个独立with/with返回值的反编译效果
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


class TestSimpleWith(unittest.TestCase):
    """测试简单with语句"""
    
    def test_simple_with(self):
        """测试简单with语句"""
        source = '''
def test_simple_with():
    with open('test.txt', 'w') as f:
        f.write('hello')
'''
        cfg = build_cfg_from_source(source, 'test_simple_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_with_no_as(self):
        """测试不带as的with语句"""
        source = '''
def test_with_no_as():
    with open('test.txt', 'w'):
        pass
'''
        cfg = build_cfg_from_source(source, 'test_with_no_as')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_with_return_value(self):
        """测试with返回值"""
        source = '''
def test_with_return():
    with open('test.txt', 'r') as f:
        return f.read()
'''
        cfg = build_cfg_from_source(source, 'test_with_return')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestMultipleWith(unittest.TestCase):
    """测试多个独立的with语句"""
    
    def test_multiple_with(self):
        """测试多个独立的with语句"""
        source = '''
def test_multiple_with():
    with open('file1.txt', 'r') as f1:
        data1 = f1.read()
    
    with open('file2.txt', 'r') as f2:
        data2 = f2.read()
    
    return data1, data2
'''
        cfg = build_cfg_from_source(source, 'test_multiple_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_multiple_with_same_file(self):
        """测试同一个文件的多次with操作"""
        source = '''
def test_multiple_same():
    with open('test.txt', 'w') as f:
        f.write('hello')
    
    with open('test.txt', 'r') as f:
        data = f.read()
    
    return data
'''
        cfg = build_cfg_from_source(source, 'test_multiple_same')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestWithInControlFlow(unittest.TestCase):
    """测试控制流中的with语句"""
    
    def test_with_in_if(self):
        """测试if语句中的with"""
        source = '''
def test_with_in_if(flag):
    if flag:
        with open('test.txt', 'r') as f:
            return f.read()
    return None
'''
        cfg = build_cfg_from_source(source, 'test_with_in_if')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_with_in_for(self):
        """测试for循环中的with"""
        source = '''
def test_with_in_for(files):
    results = []
    for filename in files:
        with open(filename, 'r') as f:
            results.append(f.read())
    return results
'''
        cfg = build_cfg_from_source(source, 'test_with_in_for')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_with_in_try(self):
        """测试try中的with"""
        source = '''
def test_with_in_try():
    try:
        with open('test.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return 'not found'
'''
        cfg = build_cfg_from_source(source, 'test_with_in_try')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestBasicWithDecompilation(unittest.TestCase):
    """测试基础with语句反编译"""
    
    def test_simple_with_decompile(self):
        """测试简单with反编译"""
        source = '''
def test_simple_with():
    with open('test.txt', 'w') as f:
        f.write('hello')
'''
        cfg = build_cfg_from_source(source, 'test_simple_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_multiple_with_decompile(self):
        """测试多个with反编译"""
        source = '''
def test_multiple_with():
    with open('file1.txt', 'r') as f1:
        data1 = f1.read()
    with open('file2.txt', 'r') as f2:
        data2 = f2.read()
    return data1, data2
'''
        cfg = build_cfg_from_source(source, 'test_multiple_with')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
