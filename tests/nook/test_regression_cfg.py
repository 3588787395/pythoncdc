"""
CFG回归测试

确保CFG模块在各种边界情况下都能正常工作。
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cfg.basic_block import BasicBlock, Instruction
from core.cfg.cfg_builder import build_cfg, CFGBuilder
from core.cfg.dominator_analyzer import DominatorAnalyzer, LoopAnalyzer
from core.cfg.structured_analyzer import StructuredAnalyzer


class TestRegressionBasicBlock(unittest.TestCase):
    """基本块回归测试"""
    
    def setUp(self):
        BasicBlock.reset_id_counter()
    
    def test_empty_block_operations(self):
        """测试空块操作"""
        block = BasicBlock()
        self.assertIsNone(block.get_first_instruction())
        self.assertIsNone(block.get_last_instruction())
        self.assertFalse(block.is_conditional())
        self.assertFalse(block.is_return())
    
    def test_single_instruction_block(self):
        """测试单指令块"""
        block = BasicBlock()
        instr = Instruction(offset=0, opcode=100, opname="LOAD_CONST", argval=42)
        block.add_instruction(instr)
        
        self.assertEqual(block.get_first_instruction(), instr)
        self.assertEqual(block.get_last_instruction(), instr)
    
    def test_block_predecessor_successor_management(self):
        """测试块前驱后继管理"""
        block1 = BasicBlock()
        block2 = BasicBlock()
        block3 = BasicBlock()
        
        block1.add_successor(block2)
        block2.add_successor(block3)
        
        self.assertIn(block2, block1.successors)
        self.assertIn(block1, block2.predecessors)
        self.assertIn(block3, block2.successors)
        
        block2.remove_successor(block3)
        self.assertNotIn(block3, block2.successors)
        self.assertNotIn(block2, block3.predecessors)


class TestRegressionCFGBuilder(unittest.TestCase):
    """CFG构建器回归测试"""
    
    def test_empty_function(self):
        """测试空函数"""
        def empty():
            pass
        
        cfg = build_cfg(empty.__code__)
        self.assertIsNotNone(cfg)
        self.assertGreaterEqual(len(cfg.blocks), 1)
    
    def test_simple_return(self):
        """测试简单返回"""
        def simple_return():
            return 42
        
        cfg = build_cfg(simple_return.__code__)
        self.assertIsNotNone(cfg.entry_block)
    
    def test_nested_if(self):
        """测试嵌套if"""
        def nested_if(x, y):
            if x > 0:
                if y > 0:
                    return 1
                return 2
            return 3
        
        cfg = build_cfg(nested_if.__code__)
        self.assertGreater(len(cfg.blocks), 3)
    
    def test_multiple_returns(self):
        """测试多个返回"""
        def multi_return(x):
            if x == 1:
                return 1
            elif x == 2:
                return 2
            elif x == 3:
                return 3
            return 0
        
        cfg = build_cfg(multi_return.__code__)
        self.assertGreater(len(cfg.blocks), 1)


class TestRegressionDominator(unittest.TestCase):
    """支配节点回归测试"""
    
    def test_linear_code_dominators(self):
        """测试线性代码的支配关系"""
        def linear():
            a = 1
            b = 2
            c = 3
            return a + b + c
        
        cfg = build_cfg(linear.__code__)
        analyzer = DominatorAnalyzer(cfg)
        analyzer.analyze()
        
        entry = cfg.entry_block
        for block in cfg.blocks.values():
            self.assertIn(entry, block.dominators)


class TestRegressionLoop(unittest.TestCase):
    """循环回归测试"""
    
    def test_nested_loops(self):
        """测试嵌套循环"""
        def nested_loops(n):
            total = 0
            for i in range(n):
                for j in range(n):
                    total += i * j
            return total
        
        cfg = build_cfg(nested_loops.__code__)
        dom_analyzer = DominatorAnalyzer(cfg)
        dom_analyzer.analyze()
        analyzer = LoopAnalyzer(cfg, dom_analyzer)
        analyzer.analyze()
        
        loops = analyzer.get_all_loops()
        self.assertGreaterEqual(len(loops), 2)


class TestRegressionEdgeCases(unittest.TestCase):
    """边界情况回归测试"""
    
    def test_function_with_exception_handling(self):
        """测试带异常处理的函数"""
        def with_exception():
            try:
                x = 1 / 0
            except ZeroDivisionError:
                x = 0
            return x
        
        cfg = build_cfg(with_exception.__code__)
        self.assertIsNotNone(cfg)
    
    def test_function_with_comprehension(self):
        """测试带推导式的函数"""
        def with_comprehension(n):
            return [x * 2 for x in range(n)]
        
        cfg = build_cfg(with_comprehension.__code__)
        self.assertIsNotNone(cfg)
    
    def test_recursive_function(self):
        """测试递归函数"""
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        
        cfg = build_cfg(factorial.__code__)
        self.assertIsNotNone(cfg)


def run_tests():
    """运行回归测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionBasicBlock))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionCFGBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionDominator))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionLoop))
    suite.addTests(loader.loadTestsFromTestCase(TestRegressionEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()
