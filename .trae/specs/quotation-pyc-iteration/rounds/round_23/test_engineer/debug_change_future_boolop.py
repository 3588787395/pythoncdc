"""Debug BoolOpRegion for change_future_real_date"""
import sys
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

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


target = find(code_obj, 'change_future_real_date')
print(f"Found: {target.co_name}")

cfg = build_cfg(target)
ra = RegionAnalyzer(cfg)
regions = ra.analyze()
print(f"Top-level regions: {len(regions)}")
for r in regions:
    print(f"\n  Region type={r.__class__.__name__}, entry_offset={r.entry.start_offset if r.entry else None}")
    if isinstance(r, BoolOpRegion):
        print(f"    is_condition_context={getattr(r, 'is_condition_context', None)}")
        print(f"    merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    op_chain:")
        for blk, op in r.op_chain:
            last = blk.get_last_instruction()
            print(f"      block@{blk.start_offset} op={op} last_instr={last.opname if last else None} -> {last.argval if last else None}")
    if isinstance(r, IfRegion):
        print(f"    cond_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks] if r.then_blocks else []}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else []}")
        print(f"    region_type={r.region_type.name if r.region_type else None}")
        if hasattr(r, 'elif_conditions') and r.elif_conditions:
            print(f"    elif_conditions={[b.start_offset for b in r.elif_conditions]}")

# Also check all regions (recursively)
print("\n=== All regions (recursive) ===")
def walk(region, depth=0):
    print(f"{'  '*depth}Region type={region.__class__.__name__}, entry_offset={region.entry.start_offset if region.entry else None}")
    if isinstance(region, BoolOpRegion):
        print(f"{'  '*depth}  is_condition_context={getattr(region, 'is_condition_context', None)}")
        print(f"{'  '*depth}  merge_block={region.merge_block.start_offset if region.merge_block else None}")
        print(f"{'  '*depth}  op_chain blocks={[b.start_offset for b, _ in region.op_chain]}")
    for child in getattr(region, 'children', []) or []:
        walk(child, depth + 1)

for r in regions:
    walk(r)
