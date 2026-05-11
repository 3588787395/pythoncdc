"""
CFG模块单元测试

测试控制流图相关的核心功能。
"""

import unittest
import types
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.cfg.basic_block import BasicBlock, Instruction
from core.cfg.cfg_builder import CFGBuilder, ControlFlowGraph, build_cfg, build_cfg_from_source
from core.cfg.dominator_analyzer import DominatorAnalyzer, LoopAnalyzer
from core.cfg.structured_analyzer import StructuredAnalyzer, ControlStructureType


class TestInstruction(unittest.TestCase):
    """测试Instruction类"""
    
    def test_instruction_creation(self):
        """测试指令创建"""
        instr = Instruction(offset=0, opcode=100, opname="LOAD_CONST", arg=1, argval=42)
        self.assertEqual(instr.offset, 0)
        self.assertEqual(instr.opcode, 100)
        self.assertEqual(instr.opname, "LOAD_CONST")
        self.assertEqual(instr.arg, 1)
        self.assertEqual(instr.argval, 42)
    
    def test_instruction_equality(self):
        """测试指令相等性"""
        instr1 = Instruction(offset=0, opcode=100, opname="LOAD_CONST")
        instr2 = Instruction(offset=0, opcode=100, opname="LOAD_CONST")
        instr3 = Instruction(offset=1, opcode=100, opname="LOAD_CONST")
        
        self.assertEqual(instr1, instr2)
        self.assertNotEqual(instr1, instr3)


class TestBasicBlock(unittest.TestCase):
    """测试BasicBlock类"""
    
    def setUp(self):
        BasicBlock.reset_id_counter()
    
    def test_block_creation(self):
        """测试基本块创建"""
        block = BasicBlock(start_offset=0)
        self.assertEqual(block.start_offset, 0)
        self.assertEqual(len(block.instructions), 0)
        self.assertEqual(len(block.predecessors), 0)
        self.assertEqual(len(block.successors), 0)
    
    def test_add_instruction(self):
        """测试添加指令"""
        block = BasicBlock()
        instr = Instruction(offset=0, opcode=100, opname="LOAD_CONST")
        block.add_instruction(instr)
        
        self.assertEqual(len(block.instructions), 1)
        self.assertEqual(block.start_offset, 0)
        self.assertEqual(block.end_offset, 0)
    
    def test_add_successor(self):
        """测试添加后继"""
        block1 = BasicBlock()
        block2 = BasicBlock()
        
        block1.add_successor(block2)
        
        self.assertIn(block2, block1.successors)
        self.assertIn(block1, block2.predecessors)
    
    def test_is_conditional(self):
        """测试条件判断"""
        block = BasicBlock()
        block.add_instruction(Instruction(offset=0, opcode=100, opname="LOAD_CONST"))
        block.add_instruction(Instruction(offset=2, opcode=114, opname="POP_JUMP_IF_FALSE", arg=10))
        
        self.assertTrue(block.is_conditional())
    
    def test_is_return(self):
        """测试返回判断"""
        block = BasicBlock()
        block.add_instruction(Instruction(offset=0, opcode=83, opname="RETURN_VALUE"))
        
        self.assertTrue(block.is_return())


class TestControlFlowGraph(unittest.TestCase):
    """测试ControlFlowGraph类"""
    
    def setUp(self):
        BasicBlock.reset_id_counter()
    
    def test_cfg_creation(self):
        """测试CFG创建"""
        cfg = ControlFlowGraph(name="test")
        self.assertEqual(cfg.name, "test")
        self.assertEqual(len(cfg.blocks), 0)
        self.assertIsNone(cfg.entry_block)
    
    def test_add_block(self):
        """测试添加基本块"""
        cfg = ControlFlowGraph()
        block = BasicBlock(start_offset=0)
        cfg.add_block(block)
        
        self.assertEqual(len(cfg.blocks), 1)
        self.assertIn(block.id, cfg.blocks)
    
    def test_set_entry_block(self):
        """测试设置入口块"""
        cfg = ControlFlowGraph()
        block = BasicBlock()
        cfg.set_entry_block(block)
        
        self.assertEqual(cfg.entry_block, block)
        self.assertTrue(block.is_entry)


class TestCFGBuilder(unittest.TestCase):
    """测试CFGBuilder类"""
    
    def test_build_simple_function(self):
        """测试构建简单函数的CFG"""
        def simple():
            x = 1
            return x
        
        builder = CFGBuilder()
        cfg = builder.build(simple.__code__, "simple")
        
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 0)
        self.assertIsNotNone(cfg.entry_block)
    
    def test_build_with_if(self):
        """测试构建带if语句的CFG"""
        def with_if(x):
            if x > 0:
                return 1
            return 0
        
        cfg = build_cfg(with_if.__code__, "with_if")
        
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 1)
    
    def test_build_with_loop(self):
        """测试构建带循环的CFG"""
        def with_loop(n):
            s = 0
            for i in range(n):
                s += i
            return s
        
        cfg = build_cfg(with_loop.__code__, "with_loop")
        
        self.assertIsNotNone(cfg)
        self.assertGreater(len(cfg.blocks), 1)


class TestDominatorAnalyzer(unittest.TestCase):
    """测试DominatorAnalyzer类"""
    
    def test_simple_dominators(self):
        """测试简单支配关系"""
        def simple():
            x = 1
            return x
        
        cfg = build_cfg(simple.__code__)
        analyzer = DominatorAnalyzer(cfg)
        analyzer.analyze()
        
        entry = cfg.entry_block
        self.assertIn(entry, entry.dominators)
    
    def test_branch_dominators(self):
        """测试分支支配关系"""
        def branch(x):
            if x > 0:
                a = 1
            else:
                a = 2
            return a
        
        cfg = build_cfg(branch.__code__)
        analyzer = DominatorAnalyzer(cfg)
        analyzer.analyze()
        
        entry = cfg.entry_block
        for block in cfg.blocks.values():
            self.assertIn(entry, block.dominators)


class TestLoopAnalyzer(unittest.TestCase):
    """测试LoopAnalyzer类"""
    
    def test_find_for_loop(self):
        """测试查找for循环"""
        def with_for():
            s = 0
            for i in range(10):
                s += i
            return s
        
        cfg = build_cfg(with_for.__code__)
        dom_analyzer = DominatorAnalyzer(cfg)
        dom_analyzer.analyze()
        analyzer = LoopAnalyzer(cfg, dom_analyzer)
        analyzer.analyze()
        
        loops = analyzer.get_all_loops()
        self.assertGreaterEqual(len(loops), 1)
    
    def test_find_while_loop(self):
        """测试查找while循环"""
        def with_while():
            i = 0
            while i < 10:
                i += 1
            return i
        
        cfg = build_cfg(with_while.__code__)
        dom_analyzer = DominatorAnalyzer(cfg)
        dom_analyzer.analyze()
        analyzer = LoopAnalyzer(cfg, dom_analyzer)
        analyzer.analyze()
        
        loops = analyzer.get_all_loops()
        self.assertGreaterEqual(len(loops), 1)


class TestStructuredAnalyzer(unittest.TestCase):
    """测试StructuredAnalyzer类"""
    
    def test_analyze_if(self):
        """测试分析if结构"""
        def with_if(x):
            if x > 0:
                return 1
            return 0
        
        cfg = build_cfg(with_if.__code__)
        analyzer = StructuredAnalyzer(cfg)
        structures = analyzer.analyze()
        
        if_structs = [s for s in structures if s.struct_type in 
                     (ControlStructureType.IF_THEN, ControlStructureType.IF_THEN_ELSE)]
        self.assertGreaterEqual(len(if_structs), 1)
    
    def test_analyze_loop(self):
        """测试分析循环结构"""
        def with_loop():
            for i in range(10):
                pass
            return 0
        
        cfg = build_cfg(with_loop.__code__)
        analyzer = StructuredAnalyzer(cfg)
        structures = analyzer.analyze()
        
        loop_structs = [s for s in structures if s.struct_type in 
                       (ControlStructureType.FOR_LOOP, ControlStructureType.WHILE_LOOP)]
        self.assertGreaterEqual(len(loop_structs), 1)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestInstruction))
    suite.addTests(loader.loadTestsFromTestCase(TestBasicBlock))
    suite.addTests(loader.loadTestsFromTestCase(TestControlFlowGraph))
    suite.addTests(loader.loadTestsFromTestCase(TestCFGBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestDominatorAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestLoopAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredAnalyzer))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_tests()
