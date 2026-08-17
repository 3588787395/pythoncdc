#!/usr/bin/env python3
"""R92 check IfRegion then_blocks for merge_block inclusion"""
import sys, marshal, types
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

for func_name in ['get_multiminute_his_data', 'get_history_common', 'get_price_common']:
    func_code = find_function(orig_code, func_name)
    if not func_code:
        continue
    builder = CFGBuilder()
    cfg = builder.build(func_code)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    
    for r in regions:
        if isinstance(r, IfRegion) and r.merge_block is not None:
            # Check if merge_block is in then_blocks
            if r.merge_block in (r.then_blocks or []):
                print(f"  {func_name}: IfRegion@{r.entry.start_offset} merge_block={r.merge_block.start_offset} "
                      f"IN then_blocks (total {len(r.then_blocks)} blocks)")
            # Check if merge_block is in blocks but not in then_blocks/else_blocks
            if r.merge_block in r.blocks and r.merge_block not in (r.then_blocks or []) and r.merge_block not in (r.else_blocks or []):
                # Check if blocks after merge_block are in blocks
                post_mb = [b for b in r.blocks if b.start_offset > r.merge_block.start_offset]
                if post_mb:
                    print(f"  {func_name}: IfRegion@{r.entry.start_offset} merge_block={r.merge_block.start_offset} "
                          f"has {len(post_mb)} blocks AFTER merge_block in region.blocks")
