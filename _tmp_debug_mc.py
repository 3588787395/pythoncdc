#!/usr/bin/env python3
"""Debug multiple_coroutines decompilation"""
import sys
import os
import types
import importlib.util

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

# Load pyc
spec = importlib.util.spec_from_file_location('test_mod', 'python_syntax_comprehensive_test.pyc')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Get code objects
import marshal
with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

for const in orig_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'multiple_coroutines':
        print(f"=== multiple_coroutines ===")
        
        builder = CFGBuilder()
        cfg = builder.build(const)
        
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        print(f"entry_block: offset={cfg.entry_block.start_offset}")
        print(f"generator_entry_block: {analyzer.metadata.get('generator_entry_block')}")
        print(f"is_generator_entry: {analyzer.metadata.get('is_generator_entry')}")
        
        # Create AST generator
        gen = RegionASTGenerator(cfg, analyzer)
        
        # Monkey-patch _reconstruct_await_block_stmts for debugging
        original = gen._reconstruct_await_block_stmts
        def debug_reconstruct(block):
            print(f"\n[_reconstruct_await_block_stmts] called for block offset={block.start_offset}")
            print(f"  instructions:")
            for i in block.instructions:
                print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")
            print(f"  successors: {[s.start_offset for s in block.successors]}")
            result = original(block)
            print(f"  result: {result}")
            return result
        
        gen._reconstruct_await_block_stmts = debug_reconstruct
        
        # Also debug _find_await_store_target
        original_find = gen._find_await_store_target
        def debug_find_target(block):
            print(f"\n[_find_await_store_target] called for block offset={block.start_offset}")
            print(f"  successors: {[s.start_offset for s in block.successors]}")
            for succ in block.successors:
                print(f"    succ {succ.start_offset}: {[(i.opname, i.argval) for i in succ.instructions]}")
                print(f"      succ's succs: {[s.start_offset for s in succ.successors]}")
            result = original_find(block)
            print(f"  result: {result}")
            return result
        
        gen._find_await_store_target = debug_find_target
        
        # Generate
        result = gen.generate()
        print(f"\n=== Generated AST ===")
        print(result)
        break
