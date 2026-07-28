"""Debug region analysis for change_future_real_date"""
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

# Walk to find the target function
def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r is not None:
                return r
    return None

target = find(code_obj, 'change_future_real_date')
print(f"Found: {target.co_name}")

cfg = build_cfg(target)
print(f"CFG blocks: {len(cfg.blocks)}")
for blk in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    print(f"  Block@{blk.start_offset} -> {[b.start_offset for b in blk.successors]}  preds={[b.start_offset for b in blk.predecessors]}")
    for ins in blk.instructions:
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        argval = getattr(ins, 'argval', None)
        print(f"    {ins.offset:4d} {ins.opname:30s} {argval}")

print("\n=== Region Analysis ===")
ra = RegionAnalyzer(cfg)
regions = ra.analyze()
print(f"Top-level regions: {len(regions)}")
for r in regions:
    print(f"  Region type={r.__class__.__name__}, entry={getattr(r, 'entry', None)}")
    if hasattr(r, 'blocks'):
        print(f"    blocks={[b.offset for b in r.blocks]}")
    if hasattr(r, 'then_blocks'):
        print(f"    then={[b.offset for b in r.then_blocks] if r.then_blocks else []}")
    if hasattr(r, 'else_blocks'):
        print(f"    else={[b.offset for b in r.else_blocks] if r.else_blocks else []}")
    if hasattr(r, 'merge_block'):
        print(f"    merge={r.merge_block.offset if r.merge_block else None}")
    if hasattr(r, 'subregions'):
        print(f"    subregions count={len(r.subregions)}")
        for sr in r.subregions:
            print(f"      subregion type={sr.__class__.__name__}, entry={getattr(sr, 'entry', None)}")
            if hasattr(sr, 'blocks'):
                print(f"        blocks={[b.offset for b in sr.blocks]}")
