"""Debug BoolOpRegion blocks for change_future_real_date."""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
import marshal

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find(co, name):
    if co.co_name == name:
        return co
    for c in co.co_consts:
        if hasattr(c, 'co_consts'):
            r = find(c, name)
            if r:
                return r
    return None

target = find(code, 'change_future_real_date')
cfg = build_cfg(target)
ra = RegionAnalyzer(cfg)
regions = ra.analyze()

def walk(region, depth=0):
    prefix = '  ' * depth
    rtype = region.__class__.__name__
    entry_off = region.entry.start_offset if region.entry else None
    print(f"{prefix}{rtype}@{entry_off}")
    if hasattr(region, 'blocks'):
        block_offs = sorted(b.start_offset for b in region.blocks)
        print(f"{prefix}  blocks={block_offs}")
    if hasattr(region, 'op_chain'):
        print(f"{prefix}  op_chain={[b.start_offset for b,_ in region.op_chain]}")
        print(f"{prefix}  merge_block={region.merge_block.start_offset if region.merge_block else None}")
    if hasattr(region, 'then_blocks'):
        print(f"{prefix}  then_blocks={[b.start_offset for b in region.then_blocks]}")
    if hasattr(region, 'else_blocks'):
        print(f"{prefix}  else_blocks={[b.start_offset for b in region.else_blocks]}")
    if hasattr(region, 'children'):
        for c in region.children:
            walk(c, depth + 1)

for r in regions:
    walk(r)
    print()
