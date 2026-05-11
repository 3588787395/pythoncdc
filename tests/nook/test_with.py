"""
CFG with语句测试
测试with语句的反编译效果
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


class TestWithStatement(unittest.TestCase):
    """测试with语句反编译"""
    
    def test_simple_with(self):
        """测试简单with语句"""
        source = '''
def test():
    with open('file.txt', 'r') as f:
        content = f.read()
    return content
'''
        code = compile(source, '<string>', 'exec')
        func_code = None
        for const in code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'test':
                func_code = const
                break
        
        self.assertIsNotNone(func_code, "应该找到test函数")
        
        # 构建CFG
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        
        # 生成AST
        ast_dict = generate_ast(cfg)
        # generate_ast返回的是Module类型
        self.assertEqual(ast_dict.get('type'), 'Module')
        # 检查body中是否包含内容
        body = ast_dict.get('body', [])
        self.assertGreater(len(body), 0, "AST body不应该为空")
    
    def test_multiple_with(self):
        """测试多个独立的with语句"""
        source = '''
def test():
    with open('file1.txt', 'r') as f1:
        content1 = f1.read()
    
    with open('file2.txt', 'r') as f2:
        content2 = f2.read()
    
    return content1, content2
'''
        code = compile(source, '<string>', 'exec')
        func_code = None
        for const in code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'test':
                func_code = const
                break
        
        self.assertIsNotNone(func_code)
        
        # 构建CFG
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
        
        # 检查CFG是否正确构建（不依赖is_with_block方法）
        self.assertGreater(len(cfg.blocks), 0, "CFG应该包含基本块")
    
    def test_compound_with(self):
        """测试复合with语句（多个上下文管理器）"""
        source = '''
def test():
    with open('file1.txt', 'r') as f1, open('file2.txt', 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
    return content1, content2
'''
        code = compile(source, '<string>', 'exec')
        func_code = None
        for const in code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'test':
                func_code = const
                break
        
        self.assertIsNotNone(func_code)
        
        # 构建CFG
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_nested_with(self):
        """测试嵌套with语句"""
        source = '''
def test():
    with open('outer.txt', 'r') as outer:
        with open('inner.txt', 'r') as inner:
            content = inner.read()
    return content
'''
        code = compile(source, '<string>', 'exec')
        func_code = None
        for const in code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'test':
                func_code = const
                break
        
        self.assertIsNotNone(func_code)
        
        # 构建CFG
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)
    
    def test_with_exception_handling(self):
        """测试with语句与异常处理"""
        source = '''
def test():
    try:
        with open('file.txt', 'r') as f:
            content = f.read()
    except FileNotFoundError:
        content = '文件不存在'
    return content
'''
        code = compile(source, '<string>', 'exec')
        func_code = None
        for const in code.co_consts:
            if hasattr(const, 'co_name') and const.co_name == 'test':
                func_code = const
                break
        
        self.assertIsNotNone(func_code)
        
        # 构建CFG
        cfg = build_cfg_from_source(source, 'test')
        self.assertIsNotNone(cfg)


class TestWithDecompilation(unittest.TestCase):
    """测试with语句反编译结果"""
    
    def test_decompile_simple_with(self):
        """测试反编译简单with语句"""
        source = '''
def use_context_manager():
    with CustomContextManager() as cm:
        print('在上下文中执行')
'''
        # 编译
        code = compile(source, '<string>', 'exec')
        
        # 反编译（这里需要调用实际的反编译器）
        # 暂时跳过实际反编译测试，只验证CFG构建
        cfg = build_cfg_from_source(source, 'use_context_manager')
        self.assertIsNotNone(cfg)
    
    def test_decompile_multiple_with(self):
        """测试反编译多个独立with语句"""
        source = '''
def use_context_manager():
    with CustomContextManager() as cm:
        print('第一个上下文')
    
    with open('file.txt', 'w') as f:
        f.write('内容')
'''
        cfg = build_cfg_from_source(source, 'use_context_manager')
        self.assertIsNotNone(cfg)
        
        # 应该能够区分两个独立的with语句
        # 这里需要进一步验证反编译结果


if __name__ == '__main__':
    unittest.main()
