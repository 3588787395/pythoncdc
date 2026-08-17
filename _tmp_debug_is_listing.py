"""Debug: check if is_listing's chained compare is recognized as IfRegion."""
import sys
import os
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

from pycdc import decompile_pyc as _decompile
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import marshal
import dis
import types

pyc_path = "F:/Downloads/pythoncdc-main/site-packages/IQEngine/core/asset.pyc"
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name, results=None):
    if results is None:
        results = []
    if code_obj.co_name == name:
        results.append(code_obj)
    for c in code_obj.co_consts:
        if isinstance(c, types.CodeType):
            find_code(c, name, results)
    return results

# Get the is_listing that has chained compare (not the NotImplementedError one)
listings = find_code(code, 'is_listing')
target_co = None
for co in listings:
    instrs = list(dis.get_instructions(co))
    has_jifop = any(i.opname == 'JUMP_IF_FALSE_OR_POP' for i in instrs)
    if has_jifop:
        target_co = co
        break

if target_co is None:
    print("No is_listing with JUMP_IF_FALSE_OR_POP found")
    sys.exit(1)

print(f"Found is_listing with {len(list(dis.get_instructions(target_co)))} instructions")

# Build CFG
builder = CFGBuilder()
cfg = builder.build_cfg(target_co)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"\nRegions found: {len(regions)}")
for r in regions:
    rtype = type(r).__name__
    entry = r.entry.start_offset if r.entry else None
    has_cc = bool(getattr(r, 'chained_compare_ops', None))
    cc_ops = getattr(r, 'chained_compare_ops', [])
    merge = getattr(r, 'merge_block', None)
    merge_offset = merge.start_offset if merge else None
    print(f"  {rtype}: entry={entry}, chained_compare_ops={cc_ops}, merge={merge_offset}")
    if hasattr(r, 'condition_block') and r.condition_block:
        cb_last = r.condition_block.get_last_instruction()
        print(f"    cond_block last: {cb_last.opname if cb_last else 'None'}")
