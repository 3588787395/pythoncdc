"""调试 _is_same_type_date 的区域结构"""
import sys
sys.path.insert(0, '/workspace')

from pycdc import decompile_pyc
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder

PYC = '/workspace/quotation.pyc'

# 加载 code object
import marshal, types
with open(PYC, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# 找到 _is_same_type_date
def find_func(c, name):
    if c.co_name == name:
        return c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            r = find_func(k, name)
            if r:
                return r
    return None

target = find_func(code, '_is_same_type_date')
print(f"Found: {target.co_name}, nlocals={target.co_nlocals}, varnames={target.co_varnames}")

# 构建 CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target)
print(f"\n=== Blocks ===")
for b in cfg.get_blocks_in_order():
    print(f"  Block @ {b.start_offset}: preds={[p.start_offset for p in b.predecessors]}, succs={[s.start_offset for s in b.successors]}")
    for ins in b.instructions:
        print(f"    {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")

# 分析区域
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
    if hasattr(r, 'children') and r.children:
        for c in r.children:
            print(f"    child: {type(c).__name__} entry={c.entry.start_offset if c.entry else None}")
    if hasattr(r, 'blocks'):
        print(f"    blocks={[b.start_offset for b in r.blocks]}")
