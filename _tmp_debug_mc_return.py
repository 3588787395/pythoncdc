#!/usr/bin/env python3
"""Debug multiple_coroutines: check if Block 132 (return results) is processed"""
import sys
import types
import importlib.util
import marshal

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

spec = importlib.util.spec_from_file_location('test_mod', 'python_syntax_comprehensive_test.pyc')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

for const in orig_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'multiple_coroutines':
        builder = CFGBuilder()
        cfg = builder.build(const)
        
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()
        
        gen = RegionASTGenerator(cfg, analyzer)
        
        # Monkey-patch _generate_block_statements to trace calls
        original_gbs = gen._generate_block_statements
        def trace_gbs(block, _cjb_parent=None):
            print(f"[_generate_block_statements] block offset={block.start_offset}")
            for i in block.instructions:
                print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
            result = original_gbs(block, _cjb_parent)
            print(f"  -> result: {result}")
            return result
        
        gen._generate_block_statements = trace_gbs
        
        result = gen.generate()
        print(f"\n=== Final result ===")
        print(result)
        break
