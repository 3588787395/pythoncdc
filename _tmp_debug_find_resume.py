#!/usr/bin/env python3
"""Debug find_generator_resume_block for simple_coroutine"""
import sys
import os
import dis
import types
import importlib.util

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BasicBlock

# Load pyc using importlib
spec = importlib.util.spec_from_file_location('test_mod', 'python_syntax_comprehensive_test.pyc')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Get the module's code object
import marshal
with open('python_syntax_comprehensive_test.pyc', 'rb') as f:
    f.read(16)  # skip header (magic + flags + timestamp/hash + source_size)
    orig_code = marshal.load(f)

# Alternative: use the module's __code__
if hasattr(mod, '__loader__') and hasattr(mod.__loader__, 'get_code'):
    orig_code = mod.__loader__.get_code('test_mod')
elif hasattr(mod, '__spec__') and hasattr(mod.__spec__, 'origin'):
    # Try to get from cached pyc
    import py_compile
    py_compile.compile('python_syntax_comprehensive_testOK.py', 'python_syntax_comprehensive_testOK.pyc', doraise=True)
    with open('python_syntax_comprehensive_testOK.pyc', 'rb') as f:
        f.read(16)
        decomp_code = marshal.load(f)

# Find target function code
for const in orig_code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'simple_coroutine':
        print(f"Found simple_coroutine")
        
        builder = CFGBuilder()
        cfg = builder.build(const)
        
        entry = cfg.entry_block
        print(f"cfg.entry_block: offset={entry.start_offset}")
        print(f"  instructions: {[(i.opname, i.argval) for i in entry.instructions]}")
        print(f"  successors: {[s.start_offset for s in entry.successors]}")
        print(f"  predecessors: {[p.start_offset for p in entry.predecessors]}")
        
        print(f"\nAll blocks:")
        for off, blk in sorted(cfg.blocks.items()):
            print(f"  offset={off}: preds={[p.start_offset for p in blk.predecessors]}, "
                  f"succs={[s.start_offset for s in blk.successors]}")
            for i in blk.instructions:
                print(f"    {i.offset:4d}: {i.opname:30s} {i.argval}")
        
        # Manually trace find_generator_resume_block
        print(f"\nTracing find_generator_resume_block(entry=Block {entry.start_offset}):")
        for block in cfg.blocks.values():
            print(f"  Checking block offset={block.start_offset}:")
            print(f"    block != entry: {block != entry}")
            print(f"    block is entry: {block is entry}")
            has_resume = any(i.opname == 'RESUME' for i in block.instructions)
            print(f"    has RESUME: {has_resume}")
            if has_resume and block != entry:
                preds = [p.start_offset for p in block.predecessors]
                print(f"    predecessors offsets: {preds}")
                has_return_gen_pred = any(p == entry for p in block.predecessors)
                print(f"    has_return_gen_pred (p == entry): {has_return_gen_pred}")
                has_return_gen_pred_is = any(p is entry for p in block.predecessors)
                print(f"    has_return_gen_pred (p is entry): {has_return_gen_pred_is}")
                if has_return_gen_pred or not block.predecessors:
                    print(f"    >>> WOULD RETURN this block (offset={block.start_offset})")
                else:
                    print(f"    >>> SKIP (no match)")
        
        # Now actually call the analyzer
        analyzer = RegionAnalyzer(cfg)
        
        # Monkey-patch to add debug output
        original_find = analyzer.find_generator_resume_block
        def debug_find(entry_block):
            print(f"\n[DEBUG] find_generator_resume_block called with entry_block offset={entry_block.start_offset}")
            result = original_find(entry_block)
            if result:
                print(f"[DEBUG] find_generator_resume_block returned block offset={result.start_offset}")
            else:
                print(f"[DEBUG] find_generator_resume_block returned None")
            return result
        
        analyzer.find_generator_resume_block = debug_find
        
        regions = analyzer.analyze()
        print(f"\nFinal metadata:")
        for k, v in analyzer.metadata.items():
            if hasattr(v, 'start_offset'):
                print(f"  {k}: block offset={v.start_offset}")
            else:
                print(f"  {k}: {v}")
        break
