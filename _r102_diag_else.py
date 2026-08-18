#!/usr/bin/env python3
"""诊断_find_try_else_blocks的执行路径"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import marshal
import types
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

pyc_path = os.path.join('.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_01', 'test_engineer', 'minimal_repros', 'repro_05_try_else_finally_return.pyc')

with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'integration_test':
        target_func = const
        break

cfg = build_cfg(target_func)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the TryExceptRegion
for r in analyzer.regions:
    if isinstance(r, TryExceptRegion):
        print(f"TryExceptRegion: try_range=({r.try_offset_start},{r.try_offset_end})")
        print(f"  try_blocks={[b.start_offset for b in r.try_blocks]}")
        print(f"  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}")
        print(f"  has_else={r.has_else} has_finally={r.has_finally}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  finally_blocks={[b.start_offset for b in r.finally_blocks]}")
        
        # Call _find_try_else_blocks directly
        else_blocks = analyzer._find_try_else_blocks(r)
        print(f"\n  _find_try_else_blocks result: {[b.start_offset for b in else_blocks]}")
        
        # Call _find_inner_else_blocks directly
        all_handler_blocks = set()
        all_handler_blocks.update(r.handler_entry_blocks)
        for _, _, hblocks in r.except_handlers:
            all_handler_blocks.update(hblocks)
        if r.finally_blocks:
            all_handler_blocks.update(r.finally_blocks)
        
        inner_else = analyzer._find_inner_else_blocks(r, r.try_offset_end, all_handler_blocks)
        print(f"  _find_inner_else_blocks result: {[b.start_offset for b in inner_else]}")
        
        # Check try_body_max_end calculation
        handler_set = set(r.handler_entry_blocks)
        try_body_max_end = 0
        for tb in r.try_blocks:
            has_exc_edge = any(s in handler_set for s in tb.successors)
            is_try_entry = tb is r.entry or tb.start_offset == r.entry.start_offset
            if has_exc_edge or is_try_entry:
                for instr in tb.instructions:
                    if instr.offset > try_body_max_end and instr.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG'):
                        try_body_max_end = instr.offset
        print(f"\n  try_body_max_end={try_body_max_end}")
        print(f"  first_handler_entry={min(b.start_offset for b in r.handler_entry_blocks)}")
        
        # Check which blocks fall in range
        for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
            if block.start_offset > try_body_max_end and block.start_offset < min(b.start_offset for b in r.handler_entry_blocks):
                in_try_body = block in set(r.try_blocks)
                in_finally = block in set(r.finally_blocks)
                print(f"    block {block.start_offset}: in_try_body={in_try_body} in_finally={in_finally} "
                      f"instrs={[i.opname for i in block.instructions if i.opname not in ('RESUME','NOP','CACHE','EXTENDED_ARG')]}")
        break
