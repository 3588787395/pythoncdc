"""
CFG集成测试

测试CFG模块与其他模块的集成。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cfg.cfg_builder import build_cfg
from core.cfg.ast_generator import generate_ast, ASTBuilder
from parsers.ast_builder_cfg import CFGASTBuilder, CFGDecompiler
from parsers.ast_builder_unified import UnifiedASTBuilder, BuilderMode


class TestCFGIntegration(unittest.TestCase):
    """测试CFG集成"""
    
    def test_cfg_to_ast_integration(self):
        """测试CFG到AST的集成"""
        def sample_func():
            x = 1
            return x
        
        cfg = build_cfg(sample_func.__code__)
        ast = generate_ast(cfg)
        
        self.assertIsNotNone(ast)
        self.assertEqual(ast['type'], 'Module')
    
    def test_builder_integration(self):
        """测试构建器集成"""
        def sample_func():
            if True:
                x = 1
            else:
                x = 2
            return x
        
        builder = CFGASTBuilder()
        ast = builder.build_from_function(sample_func)
        
        self.assertIsNotNone(ast)
        self.assertIn('body', ast)
    
    def test_decompiler_integration(self):
        """测试反编译器集成"""
        def sample_func():
            return 42
        
        decompiler = CFGDecompiler()
        source = decompiler.decompile_function(sample_func)
        
        self.assertIsNotNone(source)
        self.assertIsInstance(source, str)
    
    def test_unified_builder_cfg_mode(self):
        """测试统一构建器CFG模式"""
        def sample_func():
            x = 1
            return x
        
        builder = UnifiedASTBuilder(mode=BuilderMode.CFG)
        ast = builder.build_from_function(sample_func)
        
        self.assertIsNotNone(ast)
    
    def test_complex_function_integration(self):
        """测试复杂函数集成"""
        def complex_func(n):
            result = 0
            for i in range(n):
                if i % 2 == 0:
                    result += i
                else:
                    result -= i
            return result
        
        cfg = build_cfg(complex_func.__code__)
        self.assertGreater(len(cfg.blocks), 1)
        
        ast = generate_ast(cfg)
        self.assertIsNotNone(ast)


class TestEndToEnd(unittest.TestCase):
    """端到端测试"""
    
    def test_simple_function_e2e(self):
        """测试简单函数端到端"""
        def simple():
            return 1 + 2
        
        builder = CFGASTBuilder()
        ast = builder.build_from_function(simple)
        
        self.assertIsNotNone(ast)
        self.assertEqual(ast['type'], 'Module')
    
    def test_conditional_e2e(self):
        """测试条件语句端到端"""
        def conditional(x):
            if x > 0:
                return 1
            return 0
        
        cfg = build_cfg(conditional.__code__)
        ast = generate_ast(cfg)
        
        self.assertIsNotNone(ast)
    
    def test_loop_e2e(self):
        """测试循环端到端"""
        def loop_sum(n):
            s = 0
            for i in range(n):
                s += i
            return s
        
        cfg = build_cfg(loop_sum.__code__)
        ast = generate_ast(cfg)
        
        self.assertIsNotNone(ast)


def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestCFGIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEnd))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()
