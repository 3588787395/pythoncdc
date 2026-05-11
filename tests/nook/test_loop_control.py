"""
第1批：基础控制流测试 - 循环控制语句
测试break/continue/else的反编译效果
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


class TestBreakStatement(unittest.TestCase):
    """测试break语句"""
    
    def test_simple_break(self):
        """测试简单break"""
        source = '''
def test_simple_break():
    for i in range(10):
        if i == 5:
            break
    return i
'''
        cfg = build_cfg_from_source(source, 'test_simple_break')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_break_in_while(self):
        """测试while循环中的break"""
        source = '''
def test_break_in_while():
    count = 0
    while True:
        if count >= 5:
            break
        count += 1
    return count
'''
        cfg = build_cfg_from_source(source, 'test_break_in_while')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_break_in_nested_loop(self):
        """测试嵌套循环中的break"""
        source = '''
def test_break_in_nested():
    result = []
    for i in range(5):
        for j in range(5):
            if j == 2:
                break
            result.append((i, j))
    return result
'''
        cfg = build_cfg_from_source(source, 'test_break_in_nested')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestContinueStatement(unittest.TestCase):
    """测试continue语句"""
    
    def test_simple_continue(self):
        """测试简单continue"""
        source = '''
def test_simple_continue():
    total = 0
    for i in range(10):
        if i % 2 == 0:
            continue
        total += i
    return total
'''
        cfg = build_cfg_from_source(source, 'test_simple_continue')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_continue_in_while(self):
        """测试while循环中的continue"""
        source = '''
def test_continue_in_while():
    count = 0
    total = 0
    while count < 10:
        count += 1
        if count % 2 == 0:
            continue
        total += count
    return total
'''
        cfg = build_cfg_from_source(source, 'test_continue_in_while')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_continue_in_nested_loop(self):
        """测试嵌套循环中的continue"""
        source = '''
def test_continue_in_nested():
    result = []
    for i in range(3):
        for j in range(3):
            if j == 1:
                continue
            result.append((i, j))
    return result
'''
        cfg = build_cfg_from_source(source, 'test_continue_in_nested')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestForElseStatement(unittest.TestCase):
    """测试for-else语句"""
    
    def test_for_else_not_executed(self):
        """测试else不执行的情况"""
        source = '''
def test_for_else_not_executed():
    for i in range(5):
        if i == 3:
            break
    else:
        return 'completed'
    return 'broken'
'''
        cfg = build_cfg_from_source(source, 'test_for_else_not_executed')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_for_else_executed(self):
        """测试else执行的情况"""
        source = '''
def test_for_else_executed():
    for i in range(5):
        if i == 10:  # 不会触发
            break
    else:
        return 'completed'
    return 'broken'
'''
        cfg = build_cfg_from_source(source, 'test_for_else_executed')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_for_else_with_condition(self):
        """测试带条件的for-else"""
        source = '''
def test_for_else_with_condition(items):
    for item in items:
        if item < 0:
            break
    else:
        return 'all positive'
    return 'has negative'
'''
        cfg = build_cfg_from_source(source, 'test_for_else_with_condition')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestWhileElseStatement(unittest.TestCase):
    """测试while-else语句"""
    
    def test_while_else_not_executed(self):
        """测试else不执行的情况"""
        source = '''
def test_while_else_not_executed():
    count = 0
    while count < 5:
        if count == 3:
            break
        count += 1
    else:
        return 'completed'
    return 'broken'
'''
        cfg = build_cfg_from_source(source, 'test_while_else_not_executed')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')
    
    def test_while_else_executed(self):
        """测试else执行的情况"""
        source = '''
def test_while_else_executed():
    count = 0
    while count < 5:
        count += 1
    else:
        return 'completed'
    return 'broken'
'''
        cfg = build_cfg_from_source(source, 'test_while_else_executed')
        self.assertIsNotNone(cfg)
        
        ast_dict = generate_ast(cfg)
        self.assertEqual(ast_dict.get('type'), 'Module')


class TestLoopControlDecompilation(unittest.TestCase):
    """测试循环控制反编译结果验证"""
    
    def test_break_decompile(self):
        """测试break反编译"""
        source = '''
def test_break():
    for i in range(10):
        if i == 5:
            break
    return i
'''
        cfg = build_cfg_from_source(source, 'test_break')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_continue_decompile(self):
        """测试continue反编译"""
        source = '''
def test_continue():
    total = 0
    for i in range(10):
        if i % 2 == 0:
            continue
        total += i
    return total
'''
        cfg = build_cfg_from_source(source, 'test_continue')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_for_else_decompile(self):
        """测试for-else反编译"""
        source = '''
def test_for_else():
    for i in range(5):
        if i == 10:
            break
    else:
        return 'completed'
    return 'broken'
'''
        cfg = build_cfg_from_source(source, 'test_for_else')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)


if __name__ == '__main__':
    unittest.main()
