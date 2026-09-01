"""R30 调试 get_cb_time_info 的 for 循环体首语句丢失"""
import sys
import dis
sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion, IfRegion

PYC = '/workspace/quotation.pyc'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if isinstance(const, type(code_obj)) and const.co_name == 'get_cb_time_info':
        target = const
        break

print(f"Function: {target.co_name}")

builder = CFGBuilder()
cfg = builder.build(target)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find all LoopRegions
print(f"\n=== All LoopRegions ===")
for r in regions:
    if isinstance(r, LoopRegion):
        blocks_sorted = sorted(b.start_offset for b in r.blocks)
        print(f"\n  LoopRegion: blocks={blocks_sorted}")
        print(f"    entry: {r.entry.start_offset if r.entry else None}")
        print(f"    header_block: {r.header_block.start_offset if r.header_block else None}")
        print(f"    condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        print(f"    back_edge_block: {r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"    body_blocks: {sorted(b.start_offset for b in r.body_blocks) if r.body_blocks else None}")
        print(f"    region_type: {r.region_type}")
        nbe = r.metadata.get('natural_back_edge')
        print(f"    natural_back_edge: {nbe.start_offset if nbe else None}")

# Find the for-loop over stock_list2
# Look for blocks containing 'stock' in STORE_FAST
print(f"\n=== Blocks with 'stock' STORE_FAST ===")
for b in sorted(cfg.blocks.values(), key=lambda b: b.start_offset):
    for ins in b.instructions:
        if ins.opname == 'STORE_FAST' and ins.argval == 'stock':
            print(f"\n  Block @ {b.start_offset}:")
            for ins2 in b.instructions:
                print(f"    {ins2.offset:4d} {ins2.opname:30s} {ins2.argval!r}")
            print(f"    successors: {[s.start_offset for s in b.successors]}")
            print(f"    predecessors: {[p.start_offset for p in b.predecessors]}")
            break
