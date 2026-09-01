"""R30-3 调试：跟踪 IfRegion@342 和 IfRegion@384 的最终区域结构"""
import sys
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/core')
from cfg.cfg_builder import build_cfg
from cfg.region_analyzer import RegionAnalyzer
import marshal, struct

with open('/workspace/quotation.pyc', 'rb') as f:
    f.read(4); flags = struct.unpack('<I', f.read(4))[0]
    f.read(8); code = marshal.load(f)

def find_code(co, name):
    if co.co_name == name: return co
    for const in co.co_consts:
        if hasattr(const, 'co_name'):
            r = find_code(const, name)
            if r: return r
    return None

target = find_code(code, 'get_stock_exrights')
cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"=== All regions ({len(regions)}) ===")
for r in regions:
    print(f"  {type(r).__name__}@{r.entry.start_offset if r.entry else None} "
          f"blocks={[b.start_offset for b in r.blocks]} "
          f"parent={type(r.parent).__name__ if r.parent else None}"
          f"@{r.parent.entry.start_offset if r.parent and r.parent.entry else None}")
    if hasattr(r, 'then_blocks') and hasattr(r, 'else_blocks'):
        print(f"    then={[b.start_offset for b in r.then_blocks] if r.then_blocks else None} "
              f"else={[b.start_offset for b in r.else_blocks] if r.else_blocks else None} "
              f"merge={r.merge_block.start_offset if r.merge_block else None}")

print(f"\n=== block_to_region for blocks 342-520 ===")
for offset in [342, 384, 484, 516, 520]:
    b = cfg.get_block_by_offset(offset)
    r = analyzer.block_to_region.get(b)
    print(f"  Block@{offset} -> {type(r).__name__}@{r.entry.start_offset if r and r.entry else None}")
