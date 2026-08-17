#!/usr/bin/env python3
"""R92 debug: check merge_block object identity"""
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
    if isinstance(r, IfRegion) and r.merge_block is not None:
        mb = r.merge_block
        # Check by start_offset
        then_offsets = [b.start_offset for b in (r.then_blocks or [])]
        else_offsets = [b.start_offset for b in (r.else_blocks or [])]
        block_offsets = [b.start_offset for b in r.blocks]
        
        in_then = mb.start_offset in then_offsets
        in_else = mb.start_offset in else_offsets
        in_blocks = mb.start_offset in block_offsets
        
        if in_blocks:
            print(f"IfRegion@{r.entry.start_offset} type={r.region_type.name} merge={mb.start_offset}")
            print(f"  in_then={in_then} in_else={in_else} in_blocks={in_blocks}")
            print(f"  then_blocks offsets: {then_offsets}")
            print(f"  blocks offsets: {block_offsets}")
            
            # Check if merge_block object is the same as in then_blocks
            for i, b in enumerate(r.then_blocks or []):
                if b.start_offset == mb.start_offset:
                    print(f"  merge_block in then_blocks[{i}], same object: {b is mb}")
                    # Also check if b is a different object with same offset
                    print(f"    b.id={id(b)} mb.id={id(mb)}")
            for i, b in enumerate(r.blocks):
                if b.start_offset == mb.start_offset:
                    print(f"  merge_block in blocks[{i}], same object: {b is mb}")
                    print(f"    b.id={id(b)} mb.id={id(mb)}")
