#!/usr/bin/env python3
"""诊断repro_09"""
import sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

pyc_path = os.path.join('.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_01', 'test_engineer', 'minimal_repros', 'repro_09_try_except_else_return.pyc')
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test_try_except_else':
        target_func = const; break

cfg = build_cfg(target_func)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        print(f"try_range=({r.try_offset_start},{r.try_offset_end})")
        print(f"try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"has_else={r.has_else} has_finally={r.has_finally}")
        print(f"else_blocks={[b.start_offset for b in r.else_blocks]}")
        
        all_handler_blocks = set(r.handler_entry_blocks)
        for _, _, hblocks in r.except_handlers:
            all_handler_blocks.update(hblocks)
        if r.finally_blocks:
            all_handler_blocks.update(r.finally_blocks)
        inner_else = analyzer._find_inner_else_blocks(r, r.try_offset_end, all_handler_blocks)
        print(f"_find_inner_else_blocks: {[b.start_offset for b in inner_else]}")
        
        for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
            instrs = [(i.opname, i.argval) for i in block.instructions if i.opname not in ('RESUME','NOP','CACHE','EXTENDED_ARG')]
            succs = [s.start_offset for s in block.successors]
            print(f"  block {block.start_offset}: {instrs} succs={succs}")
        break
