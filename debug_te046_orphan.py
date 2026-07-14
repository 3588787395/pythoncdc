import sys, os
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.cfg_builder import CFGBuilder

src = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
code = compile(src, '<t>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("==== block_to_region mapping for block 158 ====")
for blk, reg in analyzer.block_to_region.items():
    if blk.start_offset == 158:
        print(f"  block {blk.start_offset} -> region {type(reg).__name__} entry={reg.entry.start_offset if reg.entry else None} parent_entry={reg.parent.entry.start_offset if (reg.parent and reg.parent.entry) else None}")

print()
print("==== top_level regions (parent is None) ====")
top_level = [r for r in analyzer.regions if r.parent is None]
for r in top_level:
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} id={id(r)}")

_top_level_ids = set(id(r) for r in top_level)
_top_level_block_sets = set()
for r in top_level:
    _top_level_block_sets.update(r.blocks)
_top_level_block_offs = sorted([b.start_offset for b in _top_level_block_sets])
print()
print("==== _top_level_block_sets (block offsets) ====")
print(_top_level_block_offs)
print("block 158 in _top_level_block_sets?", any(b.start_offset == 158 for b in _top_level_block_sets))

print()
print("==== Orphaned blocks check (replicating L607-613) ====")
orphaned = []
for _block, _region in list(analyzer.block_to_region.items()):
    if id(_region) not in _top_level_ids:
        if _block not in _top_level_block_sets:
            orphaned.append(_block.start_offset)
print("orphaned blocks (offsets):", sorted(orphaned))

print()
print("==== Block 158 instructions ====")
blk158 = cfg.blocks[158]
for ins in blk158.instructions:
    print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
print("  successors:", [s.start_offset for s in blk158.successors])

print()
print("==== Which regions contain block 158? ====")
for r in analyzer.regions:
    if any(b.start_offset == 158 for b in r.blocks):
        p = r.parent
        p_off = p.entry.start_offset if (p and p.entry) else None
        print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} parent_entry={p_off}")
