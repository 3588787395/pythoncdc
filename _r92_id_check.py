#!/usr/bin/env python3
"""R92 check if merge_block is in then_blocks for get_multiminute_his_data"""
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
        mb_id = id(r.merge_block)
        in_then = any(id(b) == mb_id for b in (r.then_blocks or []))
        in_else = any(id(b) == mb_id for b in (r.else_blocks or []))
        in_blocks = any(id(b) == mb_id for b in r.blocks)
        if in_then or in_blocks:
            print(f"IfRegion@{r.entry.start_offset} type={r.region_type.name} merge={r.merge_block.start_offset} "
                  f"in_then={in_then} in_else={in_else} in_blocks={in_blocks} "
                  f"then_count={len(r.then_blocks or [])} blocks_count={len(r.blocks)}")
