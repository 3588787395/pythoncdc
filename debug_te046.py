import sys, os, dis
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.cfg_builder import CFGBuilder

src = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
code = compile(src, '<t>', 'exec')

print("==== BYTECODE DISASSEMBLY ====")
dis.dis(code)
print()
print("co_consts:", code.co_consts)
print()

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("==== BASIC BLOCKS ====")
for bb_off, bb in cfg.blocks.items():
    print(f"=== Block {bb_off} (start={bb.start_offset}) ===")
    for ins in bb.instructions:
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval!r}")
    print(f"  successors: {[s.start_offset for s in bb.successors]}")
    print(f"  predecessors: {[p.start_offset for p in bb.predecessors]}")
    print(f"  exception_successors: {[s.start_offset for s in bb.exception_successors]}")

print()
print("==== REGIONS ====")
for r in analyzer.regions:
    print(f"=== Region type={type(r).__name__} ===")
    for attr in ('region_type', 'entry_block', 'exit_block', 'blocks', 'parent', 'children', 'handler_blocks', 'else_block', 'then_block', 'else_blocks', 'condition_block'):
        try:
            val = getattr(r, attr)
            if val is None:
                print(f"  {attr}: None")
            elif attr in ('entry_block', 'exit_block', 'parent', 'condition_block'):
                print(f"  {attr}: start_offset={val.start_offset}")
            elif attr == 'blocks':
                print(f"  {attr}: {[b.start_offset for b in val] if val else None}")
            elif attr == 'children':
                print(f"  {attr}: {[c.start_offset if hasattr(c, 'start_offset') else c for c in val] if val else None}")
            else:
                print(f"  {attr}: {val}")
        except Exception as e:
            print(f"  {attr}: <err {e}>")

print()
print("==== DUMP REGION FIELDS ====")
if analyzer.regions:
    r0 = analyzer.regions[0]
    print("Region class:", type(r0).__name__)
    print("dir:", [x for x in dir(r0) if not x.startswith('_')])
