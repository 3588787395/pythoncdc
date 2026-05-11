"""
CFG复杂代码模式测试

测试CFG模块处理复杂代码模式的能力。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cfg.cfg_builder import build_cfg
from core.cfg.ast_generator_v2 import generate_ast_v2, ExpressionReconstructor
from core.cfg.basic_block import Instruction


class TestComplexExpressions(unittest.TestCase):
    """测试复杂表达式"""
    
    def test_binary_operations(self):
        """测试二元操作"""
        def test_func():
            a = 1 + 2
            b = 3 - 4
            c = 5 * 6
            d = 7 / 8
            return a + b + c + d
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
        self.assertGreater(len(ast['body']), 0)
    
    def test_comparison_operations(self):
        """测试比较操作"""
        def test_func(x, y):
            if x > 0 and y < 10:
                return True
            return False
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_nested_calls(self):
        """测试嵌套函数调用"""
        def test_func():
            return len(str(abs(-5)))
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')


class TestComplexControlFlow(unittest.TestCase):
    """测试复杂控制流"""
    
    def test_nested_if(self):
        """测试嵌套if语句"""
        def test_func(x, y):
            if x > 0:
                if y > 0:
                    return 1
                else:
                    return 2
            else:
                return 3
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
        self.assertGreater(len(cfg.blocks), 3)
    
    def test_elif_chain(self):
        """测试elif链"""
        def test_func(x):
            if x == 1:
                return 'one'
            elif x == 2:
                return 'two'
            elif x == 3:
                return 'three'
            else:
                return 'other'
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_while_with_break(self):
        """测试带break的while循环"""
        def test_func(n):
            i = 0
            while i < n:
                if i == 5:
                    break
                i += 1
            return i
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_for_with_continue(self):
        """测试带continue的for循环"""
        def test_func(n):
            s = 0
            for i in range(n):
                if i % 2 == 0:
                    continue
                s += i
            return s
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')


class TestDataStructures(unittest.TestCase):
    """测试数据结构"""
    
    def test_list_operations(self):
        """测试列表操作"""
        def test_func():
            lst = [1, 2, 3]
            lst.append(4)
            return lst[0]
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_dict_operations(self):
        """测试字典操作"""
        def test_func():
            d = {'a': 1, 'b': 2}
            d['c'] = 3
            return d['a']
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')


class TestExceptionHandling(unittest.TestCase):
    """测试异常处理"""
    
    def test_try_except(self):
        """测试try-except"""
        def test_func():
            try:
                x = 1 / 0
            except ZeroDivisionError:
                x = 0
            return x
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_try_finally(self):
        """测试try-finally"""
        def test_func():
            try:
                x = 1
            finally:
                x = 0
            return x
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')


class TestExpressionReconstructor(unittest.TestCase):
    """测试表达式重建器"""
    
    def test_simple_arithmetic(self):
        """测试简单算术"""
        reconstructor = ExpressionReconstructor()
        instructions = [
            Instruction(offset=0, opcode=100, opname="LOAD_CONST", arg=0, argval=1),
            Instruction(offset=2, opcode=100, opname="LOAD_CONST", arg=1, argval=2),
            Instruction(offset=4, opcode=23, opname="BINARY_ADD"),
        ]
        expr = reconstructor.reconstruct(instructions)
        self.assertIsNotNone(expr)
        self.assertEqual(expr['type'], 'BinOp')
        self.assertEqual(expr['op'], '+')
    
    def test_variable_load(self):
        """测试变量加载"""
        reconstructor = ExpressionReconstructor()
        instructions = [
            Instruction(offset=0, opcode=116, opname="LOAD_GLOBAL", arg=0, argval="len"),
            Instruction(offset=2, opcode=124, opname="LOAD_FAST", arg=0, argval="x"),
            Instruction(offset=4, opcode=131, opname="CALL_FUNCTION", arg=1),
        ]
        expr = reconstructor.reconstruct(instructions)
        self.assertIsNotNone(expr)
        self.assertEqual(expr['type'], 'Call')


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_empty_function(self):
        """测试空函数"""
        def test_func():
            pass
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_single_return(self):
        """测试单条返回"""
        def test_func():
            return 42
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')
    
    def test_multiple_returns(self):
        """测试多个返回"""
        def test_func(x):
            if x > 0:
                return 1
            elif x < 0:
                return -1
            return 0
        
        cfg = build_cfg(test_func.__code__)
        ast = generate_ast_v2(cfg)
        self.assertEqual(ast['type'], 'Module')


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestComplexExpressions))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexControlFlow))
    suite.addTests(loader.loadTestsFromTestCase(TestDataStructures))
    suite.addTests(loader.loadTestsFromTestCase(TestExceptionHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestExpressionReconstructor))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()
