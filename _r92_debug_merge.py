#!/usr/bin/env python3
"""R92 debug: check merge_block 2710 in IfRegion@0 blocks"""
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

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        print(f"IfRegion@0 merge={r.merge_block.start_offset}")
        print(f"merge_block type: {type(r.merge_block)}")
        print(f"merge_block start_offset: {r.merge_block.start_offset}")
        
        block_offsets = [b.start_offset for b in r.blocks]
        then_offsets = [b.start_offset for b in (r.then_blocks or [])]
        
        print(f"blocks offsets: {block_offsets}")
        print(f"then_blocks offsets: {then_offsets}")
        
        mb_offset = r.merge_block.start_offset
        print(f"\nmerge_block {mb_offset} in blocks: {mb_offset in block_offsets}")
        print(f"merge_block {mb_offset} in then_blocks: {mb_offset in then_offsets}")
        
        # Check if 2710 is the merge_block or 2758
        print(f"\nblocks containing 2710: {[b for b in r.blocks if b.start_offset == 2710]}")
        print(f"then_blocks containing 2710: {[b for b in (r.then_blocks or []) if b.start_offset == 2710]}")
        print(f"blocks containing 2758: {[b for b in r.blocks if b.start_offset == 2758]}")
        print(f"then_blocks containing 2758: {[b for b in (r.then_blocks or []) if b.start_offset == 2758]}")
        
        # Check what's in then_blocks at/after merge
        post_mb = [b.start_offset for b in (r.then_blocks or []) if b.start_offset >= mb_offset]
        print(f"\nthen_blocks at/after merge ({mb_offset}): {post_mb}")
