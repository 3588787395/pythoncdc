"""调试 dict_to_dataframe 的区域结构"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder

import marshal, types
with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_func(c, name):
    if c.co_name == name:
        return c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            r = find_func(k, name)
            if r:
                return r
    return None

target = find_func(code, 'dict_to_dataframe')
print(f"Found: {target.co_name}, nlocals={target.co_nlocals}, varnames={target.co_varnames}")

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)
print(f"\n=== Blocks ===")
for b in cfg.get_blocks_in_order():
    print(f"  Block @ {b.start_offset}: preds={[p.start_offset for p in b.predecessors]}, succs={[s.start_offset for s in b.successors]}")
    for ins in b.instructions:
        print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f"\n=== Regions ({len(regions)}) ===")
for r in regions:
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None}")
    if hasattr(r, 'then_blocks'):
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block={r.condition_block.start_offset}")
    if hasattr(r, 'init_blocks') and r.init_blocks:
        print(f"    init_blocks={[b.start_offset for b in r.init_blocks]}")
    if hasattr(r, 'body_blocks') and r.body_blocks:
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'metadata') and r.metadata:
        print(f"    metadata={dict((k, v.start_offset if hasattr(v, 'start_offset') else v) for k, v in r.metadata.items() if not isinstance(v, (list, set)))}")
    if hasattr(r, 'blocks'):
        print(f"    blocks={[b.start_offset for b in r.blocks]}")
