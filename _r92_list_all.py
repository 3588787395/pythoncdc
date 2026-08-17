#!/usr/bin/env python3
"""R92 debug: list ALL IfRegions for get_multiminute_his_data"""
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
    if isinstance(r, IfRegion):
        mb = r.merge_block.start_offset if r.merge_block else None
        print(f"IfRegion@{r.entry.start_offset} type={r.region_type.name} merge={mb} "
              f"then={len(r.then_blocks or [])} else={len(r.else_blocks or [])} blocks={len(r.blocks)}")
        if mb is not None:
            block_offsets = [b.start_offset for b in r.blocks]
            if mb in block_offsets:
                print(f"  ** merge_block {mb} IS in blocks **")
