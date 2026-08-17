#!/usr/bin/env python3
"""R91 check IfRegion structure for get_price_common"""
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

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find the IfRegion that contains offset 278 (the JUMP_FORWARD)
for r in regions:
    if isinstance(r, IfRegion):
        block_offsets = [b.start_offset for b in r.blocks]
        if 232 in block_offsets or 278 in block_offsets:
            print(f"IfRegion: entry={r.entry.start_offset if r.entry else '?'}, cond={r.condition_block.start_offset if r.condition_block else '?'}")
            print(f"  then_blocks: {[b.start_offset for b in r.then_blocks][:10]}")
            print(f"  else_blocks: {[b.start_offset for b in r.else_blocks][:20]}")
            print(f"  total blocks: {len(r.blocks)}")
            break
