"""Dump region structure for get_cb_calender_info around offset 1120."""
import sys, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion
from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find(c, name)
            if r:
                return r
    return None

fn = find(code_obj, 'get_cb_calender_info')

cfg = CFGBuilder().build(fn)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find TryExceptRegion containing blocks around 1138
def walk(region, depth=0):
    prefix = '  ' * depth
    rtype = region.__class__.__name__
    entry_off = region.entry.start_offset if region.entry else None
    blocks = sorted(b.start_offset for b in getattr(region, 'blocks', []))
    
    # Only print regions that contain blocks near 1120-1140
    if any(1100 <= b <= 1200 for b in blocks) or entry_off in range(1100, 1200):
        print(f"{prefix}{rtype}@{entry_off} blocks={blocks}")
        if hasattr(region, 'try_blocks') and region.try_blocks:
            print(f"{prefix}  try_blocks={sorted(b.start_offset for b in region.try_blocks)}")
        if hasattr(region, 'except_handlers') and region.except_handlers:
            for h in region.except_handlers:
                print(f"{prefix}  except_handler: {h}")
        if hasattr(region, 'else_blocks') and region.else_blocks:
            print(f"{prefix}  else_blocks={sorted(b.start_offset for b in region.else_blocks)}")
        if hasattr(region, 'finally_blocks') and region.finally_blocks:
            print(f"{prefix}  finally_blocks={sorted(b.start_offset for b in region.finally_blocks)}")
    
    for child in getattr(region, 'children', []):
        walk(child, depth + 1)

for r in analyzer.regions:
    walk(r)

# Dump block 1120
print("\n=== Block@1120 ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    if 1110 <= b.start_offset <= 1145:
        print(f"Block@{b.start_offset}:")
        for ins in b.instructions:
            argrepr = getattr(ins, 'argrepr', str(ins.argval) if ins.argval is not None else '')
            print(f"  {ins.offset:4d} {ins.opname:30s} {argrepr}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")
        print(f"  predecessors: {[s.start_offset for s in b.predecessors]}")
        print()

# Check which region owns block 1120
b1120 = cfg.get_block_by_offset(1120)
if b1120:
    r1120 = analyzer.get_region_for_block(b1120)
    print(f"Block@1120 owned by: {r1120.__class__.__name__ if r1120 else 'None'}")
    if r1120:
        print(f"  region entry: {r1120.entry.start_offset if r1120.entry else None}")
        print(f"  region blocks: {sorted(b.start_offset for b in getattr(r1120, 'blocks', []))}")

# Check body_blocks of LoopRegion@492
for r in analyzer.regions:
    if hasattr(r, 'header_block') and r.header_block and r.header_block.start_offset == 492:
        print(f"\nLoopRegion@492 body_blocks: {sorted(b.start_offset for b in r.body_blocks) if r.body_blocks else 'None'}")
        print(f"  back_edge_block: {r.back_edge_block.start_offset if r.back_edge_block else None}")
        # Check if 1120 is in body_blocks
        if r.body_blocks:
            b1120_in_body = any(b.start_offset == 1120 for b in r.body_blocks)
            print(f"  1120 in body_blocks: {b1120_in_body}")
            # Check the order of body_blocks
            body_order = [b.start_offset for b in r.body_blocks]
            print(f"  body_blocks order: {body_order[:30]}...")
        break

# Check the TryExceptRegion@1138
for r in analyzer.regions:
    if r.__class__.__name__ == 'TryExceptRegion' and r.entry and r.entry.start_offset == 1138:
        print(f"\nTryExceptRegion@1138:")
        print(f"  entry: {r.entry.start_offset}")
        print(f"  try_blocks: {sorted(b.start_offset for b in r.try_blocks)}")
        # Check if 1120 is in try_blocks
        b1120_in_try = any(b.start_offset == 1120 for b in r.try_blocks)
        print(f"  1120 in try_blocks: {b1120_in_try}")
        # Check predecessors of entry
        print(f"  entry predecessors: {[p.start_offset for p in r.entry.predecessors]}")
        break
