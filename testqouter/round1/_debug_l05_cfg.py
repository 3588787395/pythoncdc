import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import py_compile, marshal

test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_l05_while_continue.py')
pyc_file = test_file + 'c'
py_compile.compile(test_file, pyc_file, doraise=True)

code = marshal.load(open(pyc_file, 'rb'))
code = code[12:]
co = marshal.loads(code)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

builder = CFGBuilder()
cfg = builder.build(co)

print("=== CFG BLOCKS ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print(f"  Block offset={b.start_offset}, succs={[s.start_offset for s in b.successors]}, preds={[p.start_offset for p in b.predecessors]}")
    for inst in b.instructions:
        print(f"    {inst.offset:4d} {inst.opname:30s} {inst.argrepr if inst.argrepr else ''}")
    print()

analyzer = RegionAnalyzer(cfg, co)
regions = analyzer.analyze()

print("=== REGIONS ===")
for r in analyzer.regions:
    rtype = r.__class__.__name__
    blocks_str = [b.start_offset for b in r.blocks]
    if isinstance(r, LoopRegion):
        print(f"  {rtype}: blocks={blocks_str}")
        print(f"    region_type={r.region_type}")
        print(f"    header_block={r.header_block.start_offset if r.header_block else None}")
        print(f"    back_edge_block={r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"    body_blocks={[b.start_offset for b in r.body_blocks]}")
        print(f"    condition_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"    else_blocks={[b.start_offset for b in r.else_blocks]}")
    else:
        print(f"  {rtype}: blocks={blocks_str}")

print("\n=== BLOCK ROLES ===")
for offset, role in sorted(analyzer.block_roles.items()):
    print(f"  Block {offset}: {role.name}")

print("\n=== BLOCK TO REGION ===")
for block, region in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
    print(f"  Block {block.start_offset} -> {region.__class__.__name__} (entry={region.entry.start_offset if region.entry else None})")

os.remove(pyc_file)
