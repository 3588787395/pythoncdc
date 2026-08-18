#!/usr/bin/env python3
"""诊断repro_r2_09的区域分析"""
import sys, os, marshal, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion, LoopRegion

pyc_path = os.path.join('.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_02', 'test_engineer', 'minimal_repros', 'repro_r2_09_multi_elif_break.pyc')
with open(pyc_path, 'rb') as f:
    f.read(16); code = marshal.load(f)
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test_multi_elif_break':
        target_func = const; break

cfg = build_cfg(target_func)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

for r in analyzer.regions:
    cls = type(r).__name__
    entry_off = r.entry.start_offset if r.entry is not None else None
    if isinstance(r, IfRegion):
        print(f"[{cls}] entry={entry_off}")
        print(f"  region_type={r.region_type}")
        print(f"  condition_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"  then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  elif_conditions={[b.start_offset for b in r.elif_conditions] if r.elif_conditions else None}")
        print(f"  elif_bodies={[[b.start_offset for b in bb] for bb in r.elif_bodies] if r.elif_bodies else None}")
        print(f"  elif_final_else={[b.start_offset for b in r.elif_final_else] if r.elif_final_else else None}")
        print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
        # Check block roles
        for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
            role = analyzer.get_block_role(b)
            if role:
                print(f"  block {b.start_offset} role={role}")
    elif isinstance(r, LoopRegion):
        print(f"[{cls}] entry={entry_off}")
        print(f"  body_blocks={[b.start_offset for b in r.body_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
    else:
        print(f"[{cls}] entry={entry_off}")
