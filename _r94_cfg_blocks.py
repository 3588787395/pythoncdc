#!/usr/bin/env python3
"""R94: Dump CFG blocks for get_kline_by_date_one"""
import sys, types, marshal, dis
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/klinedata.pyc"

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

orig_code = load_pyc(pyc_path)

def extract_code_objects(code):
    result = {code.co_name: code}
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
co = orig_map['get_kline_by_date_one']

# Build CFG
cfg = build_cfg(co)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Print all blocks
print(f"=== CFG for get_kline_by_date_one ===")
print(f"Total blocks: {len(cfg.blocks)}")
for block in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    role = analyzer.get_block_role(block) if hasattr(analyzer, 'get_block_role') else 'N/A'
    print(f"\nBlock@{block.start_offset} (role={role}, {len(block.instructions)} instrs)")
    for instr in block.instructions:
        argval = instr.argval
        if isinstance(argval, str) and len(argval) > 40:
            argval = argval[:40] + '...'
        print(f"  off={instr.offset} {instr.opname}({argval})")
    if block.successors:
        print(f"  succs: {[s.start_offset for s in block.successors]}")

# Print regions
print(f"\n=== Regions ===")
for region in analyzer.regions:
    rtype = region.region_type if hasattr(region, 'region_type') else type(region).__name__
    blocks = [b.start_offset for b in getattr(region, 'blocks', [])]
    print(f"  {rtype}: blocks={blocks}")
    if hasattr(region, 'try_blocks'):
        print(f"    try_blocks: {[b.start_offset for b in (region.try_blocks or [])]}")
    if hasattr(region, 'except_handlers'):
        print(f"    except_handlers: {region.except_handlers}")
    if hasattr(region, 'handler_blocks'):
        print(f"    handler_blocks: {[b.start_offset for b in (region.handler_blocks or [])]}")
