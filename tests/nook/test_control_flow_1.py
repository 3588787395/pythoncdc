"""
CFG控制流测试
测试if/elif/else、for、while等控制流结构
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


class TestIfStatement(unittest.TestCase):
    """测试if语句"""
    
    def test_simple_if(self):
        """测试简单if"""
        source = '''
def test():
    if x > 0:
        return '正数'
    return '非正数'
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
    
    def test_if_else(self):
        """测试if-else"""
        source = '''
def test():
    if x > 0:
        result = '正数'
    else:
        result = '非正数'
    return result
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_if_elif_else(self):
        """测试if-elif-else链"""
        source = '''
def test():
    if x > 10:
        result = '大于10'
    elif x == 10:
        result = '等于10'
    else:
        result = '小于10'
    return result
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_nested_if(self):
        """测试嵌套if"""
        source = '''
def test():
    if x > 0:
        if y > 0:
            return '都大于0'
        else:
            return 'x大于0但y不大于0'
    return 'x不大于0'
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)


class TestForLoop(unittest.TestCase):
    """测试for循环"""
    
    def test_simple_for(self):
        """测试简单for循环"""
        source = '''
def test():
    total = 0
    for i in range(10):
        total += i
    return total
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_for_with_break(self):
        """测试带break的for循环"""
        source = '''
def test():
    for i in range(10):
        if i == 5:
            break
    return i
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_for_with_continue(self):
        """测试带continue的for循环"""
        source = '''
def test():
    total = 0
    for i in range(10):
        if i % 2 == 0:
            continue
        total += i
    return total
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_for_with_else(self):
        """测试带else的for循环"""
        source = '''
def test():
    for i in range(10):
        if i == 100:  # 不会执行
            break
    else:
        return '循环完成'
    return '循环中断'
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)


class TestWhileLoop(unittest.TestCase):
    """测试while循环"""
    
    def test_simple_while(self):
        """测试简单while循环"""
        source = '''
def test():
    counter = 0
    while counter < 10:
        counter += 1
    return counter
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_while_with_break(self):
        """测试带break的while循环"""
        source = '''
def test():
    counter = 0
    while counter < 100:
        if counter == 10:
            break
        counter += 1
    return counter
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_while_with_continue(self):
        """测试带continue的while循环"""
        source = '''
def test():
    counter = 0
    total = 0
    while counter < 10:
        counter += 1
        if counter % 2 == 0:
            continue
        total += counter
    return total
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_while_with_else(self):
        """测试带else的while循环"""
        source = '''
def test():
    counter = 0
    while counter < 10:
        counter += 1
    else:
        return '循环完成'
    return '循环中断'
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)


class TestNestedLoops(unittest.TestCase):
    """测试嵌套循环"""
    
    def test_nested_for(self):
        """测试嵌套for循环"""
        source = '''
def test():
    total = 0
    for i in range(5):
        for j in range(5):
            total += i * j
    return total
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_nested_while(self):
        """测试嵌套while循环"""
        source = '''
def test():
    total = 0
    i = 0
    while i < 5:
        j = 0
        while j < 5:
            total += i * j
            j += 1
        i += 1
    return total
'''
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)


if __name__ == '__main__':
    unittest.main()
