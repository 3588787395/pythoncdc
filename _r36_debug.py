#!/usr/bin/env python3
"""Debug: trace which code path generates the else blocks in get_trading_schedule."""

import sys, os, marshal, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, TernaryRegion, BoolOpRegion, LoopRegion
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

gts = find_code(code, 'get_trading_schedule')

builder = CFGBuilder()
cfg = builder.build(gts)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Check children of IfRegion@66
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 66:
        print(f"IfRegion@66 children:")
        for c in (r.children or []):
            print(f"  {type(c).__name__}@{c.entry.start_offset if c.entry else None}")
            if isinstance(c, LoopRegion):
                print(f"    blocks={[b.start_offset for b in c.blocks]}")
                print(f"    body_blocks={[b.start_offset for b in c.body_blocks] if hasattr(c, 'body_blocks') else 'N/A'}")

        # Check if block 316 is in generated_blocks after then branch generation
        ast_gen = RegionASTGenerator(cfg, analyzer)
        
        # Manually call _if_generate_then_branch and check generated_blocks
        print(f"\nBefore then branch generation:")
        print(f"  block@316 in generated_blocks: {cfg.get_block_by_offset(316) in ast_gen.generated_blocks}")
        
        then_stmts = ast_gen._if_generate_then_branch(r)
        print(f"\nAfter then branch generation:")
        print(f"  block@316 in generated_blocks: {cfg.get_block_by_offset(316) in ast_gen.generated_blocks}")
        print(f"  block@360 in generated_blocks: {cfg.get_block_by_offset(360) in ast_gen.generated_blocks}")
        print(f"  block@362 in generated_blocks: {cfg.get_block_by_offset(362) in ast_gen.generated_blocks}")
        print(f"  then_stmts = {then_stmts}")
        
        # Now try else branch
        else_stmts = ast_gen._if_generate_else_branch(r)
        print(f"\nAfter else branch generation:")
        print(f"  else_stmts = {else_stmts}")
