#!/usr/bin/env python3
"""Debug: trace else branch generation for is_stock_trade_trigger."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

PYC_PATH = os.path.join(HERE, 'site-packages', 'IQEngine', 'utils', 'trade_schedule.pyc')

with open(PYC_PATH, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            sub = find_code(const, name)
            if sub:
                return sub
    return None

stt = find_code(code, 'is_stock_trade_trigger')

builder = CFGBuilder()
cfg = builder.build(stt)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find IfRegion@102
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 102:
        ifr = r
        break

print(f"IfRegion@102:")
print(f"  region_type={ifr.region_type}")
print(f"  then_blocks={[b.start_offset for b in ifr.then_blocks]}")
print(f"  else_blocks={[b.start_offset for b in ifr.else_blocks]}")
print(f"  children={[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (ifr.children or [])]}")

ast_gen = RegionASTGenerator(cfg, analyzer)

# Generate then branch
print(f"\n=== Generating then branch ===")
then_stmts = ast_gen._if_generate_then_branch(ifr)
for i, s in enumerate(then_stmts):
    t = s.get('type', '?') if isinstance(s, dict) else '?'
    print(f"  [{i}] type={t}")

print(f"\n  generated_blocks after then: {sorted(b.start_offset for b in ast_gen.generated_blocks)}")

# Generate else branch
print(f"\n=== Generating else branch ===")
else_stmts = ast_gen._if_generate_else_branch(ifr)
print(f"  else_stmts = {else_stmts}")
if else_stmts:
    for i, s in enumerate(else_stmts):
        t = s.get('type', '?') if isinstance(s, dict) else '?'
        print(f"  [{i}] type={t}")
        if t == 'If':
            print(f"    test={s.get('test')}")
            print(f"    body={s.get('body')}")
            print(f"    orelse={s.get('orelse')}")
