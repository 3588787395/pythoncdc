"""Debug region analysis for get_block_stocks"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

PYC = '/workspace/quotation.pyc'
module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r is not None:
                return r
    return None

target = find(code_obj, 'get_block_stocks')
print(f"Found: {target.co_name}")

cfg = build_cfg(target)
print(f"CFG blocks: {len(cfg.blocks)}")
for blk in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    print(f"  Block@{blk.start_offset}-{blk.end_offset} -> {[b.start_offset for b in blk.successors]}  preds={[b.start_offset for b in blk.predecessors]}")
    for ins in blk.instructions:
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        argval = getattr(ins, 'argval', None)
        print(f"    {ins.offset:4d} {ins.opname:30s} {argval}")

print("\n=== Region Analysis ===")
ra = RegionAnalyzer(cfg)
regions = ra.analyze()
print(f"Top-level regions: {len(regions)}")

def dump_region(r, indent=0):
    prefix = "  " * indent
    entry_off = getattr(r, 'entry', None)
    if entry_off is not None:
        entry_off = entry_off.start_offset
    print(f"{prefix}Region type={r.__class__.__name__}, entry={entry_off}")
    if hasattr(r, 'blocks'):
        print(f"{prefix}  blocks={[b.start_offset for b in r.blocks]}")
    if hasattr(r, 'then_blocks'):
        print(f"{prefix}  then={[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
    if hasattr(r, 'else_blocks'):
        print(f"{prefix}  else={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f"{prefix}  merge={r.merge_block.start_offset}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"{prefix}  cond={r.condition_block.start_offset}")
    if hasattr(r, 'body_block') and r.body_block:
        print(f"{prefix}  body={r.body_block.start_offset}")
    if hasattr(r, 'subregions'):
        for sr in r.subregions:
            dump_region(sr, indent + 1)

for r in regions:
    dump_region(r)
