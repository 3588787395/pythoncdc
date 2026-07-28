"""Debug _boolop_resolve_merge for change_future_real_date"""
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

# Manually construct chain
b36 = cfg.get_block_by_offset(36)
b124 = cfg.get_block_by_offset(124)
chain = [(b36, 'and'), (b124, 'and')]
merge = ra._boolop_resolve_merge(chain)
print(f"_boolop_resolve_merge returned: {merge.start_offset if merge else None}")

# Show instructions of merge
if merge:
    print(f"\nMerge block @{merge.start_offset} instructions:")
    for ins in merge.instructions:
        if ins.opname in ('EXTENDED_ARG', 'CACHE'):
            continue
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval}")

# Now run full analysis
regions = ra.analyze()
print(f"\nTop-level regions: {len(regions)}")
for r in regions:
    if isinstance(r, BoolOpRegion):
        print(f"\nBoolOpRegion entry={r.entry.start_offset}")
        print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
        print(f"  is_condition_context={getattr(r, 'is_condition_context', None)}")
        print(f"  op_chain blocks={[b.start_offset for b, _ in r.op_chain]}")
        for blk, op in r.op_chain:
            last = blk.get_last_instruction()
            print(f"    block@{blk.start_offset} op={op} last={last.opname if last else None} target={last.argval if last else None}")
