"""调试 get_balance_statement 的区域结构"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion, IfRegion, BoolOpRegion, LoopRegion
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

target = find_func(code, 'get_balance_statement')
print(f"Found: {target.co_name}")

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
print(f"\n=== Regions ({len(regions)}) ===")
for r in regions:
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None}")
    if hasattr(r, 'condition_block') and r.condition_block:
        print(f"    condition_block={r.condition_block.start_offset}")
    if hasattr(r, 'then_blocks'):
        print(f"    then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
    if hasattr(r, 'blocks'):
        print(f"    blocks={[b.start_offset for b in r.blocks]}")
    if isinstance(r, MatchRegion):
        print(f"    subject_block={getattr(r, 'subject_block', None)}")
        print(f"    case_blocks={getattr(r, 'case_blocks', None)}")
        print(f"    metadata={r.metadata}")
