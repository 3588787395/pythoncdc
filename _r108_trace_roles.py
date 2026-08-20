"""Trace how Block@366 and Block@194 get BREAK role in validate_data."""
import sys, dis, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole

# Load original bytecode
f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
vd = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'validate_data'][0]

# Build CFG
builder = CFGBuilder()
cfg = builder.build(vd)

# Analyze regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

blocks = list(cfg.blocks.values())

# Find the loop
for r in analyzer.regions:
    entry = getattr(r, 'entry_block', None)
    if entry is None:
        entry = getattr(r, 'header_block', None)
    print(f"Region: {type(r).__name__}, entry={entry.start_offset if entry else 'N/A'}")
    if hasattr(r, 'header_block') and r.header_block:
        print(f"  header={r.header_block.start_offset}")
    if hasattr(r, 'body_blocks'):
        print(f"  body_blocks={[b.start_offset for b in r.body_blocks]}")
    if hasattr(r, 'break_blocks'):
        print(f"  break_blocks={[b.start_offset for b in r.break_blocks]}")
    if hasattr(r, 'metadata'):
        lbfs = r.metadata.get('loop_body_full_set', None)
        if lbfs:
            print(f"  loop_body_full_set={[b.start_offset for b in lbfs]}")

print("\n=== Block roles ===")
for b in sorted(blocks, key=lambda x: x.start_offset):
    role = analyzer.get_block_role(b)
    print(f"  Block@{b.start_offset}: role={role}")

print("\n=== Block@366 details ===")
b366 = cfg.get_block_by_offset(366)
print(f"  instructions: {[(i.offset, i.opname, i.argval) for i in b366.instructions]}")
print(f"  successors: {[s.start_offset for s in b366.successors]}")
print(f"  role: {analyzer.get_block_role(b366)}")

print("\n=== Block@194 details ===")
b194 = cfg.get_block_by_offset(194)
print(f"  instructions: {[(i.offset, i.opname, i.argval) for i in b194.instructions]}")
print(f"  successors: {[s.start_offset for s in b194.successors]}")
print(f"  role: {analyzer.get_block_role(b194)}")

print("\n=== Block@406 details ===")
b406 = cfg.get_block_by_offset(406)
print(f"  instructions: {[(i.offset, i.opname, i.argval) for i in b406.instructions]}")
print(f"  successors: {[s.start_offset for s in b406.successors]}")
print(f"  role: {analyzer.get_block_role(b406)}")

print("\n=== Block@238 details ===")
b238 = cfg.get_block_by_offset(238)
print(f"  instructions: {[(i.offset, i.opname, i.argval) for i in b238.instructions]}")
print(f"  successors: {[s.start_offset for s in b238.successors]}")
print(f"  role: {analyzer.get_block_role(b238)}")

# Check which blocks have block 366 or 194 as successor
print("\n=== Predecessors of Block@366 ===")
for p in b366.predecessors:
    print(f"  Block@{p.start_offset}: last_instr={p.get_last_instruction().opname if p.get_last_instruction() else None}")

print("\n=== Predecessors of Block@194 ===")
for p in b194.predecessors:
    print(f"  Block@{p.start_offset}: last_instr={p.get_last_instruction().opname if p.get_last_instruction() else None}")

# Check the loop region
for r in analyzer.regions:
    if hasattr(r, 'header_block') and r.header_block and r.header_block.start_offset == 72:
        print(f"\n=== Loop Region (header@72) ===")
        print(f"  body_blocks={[b.start_offset for b in r.body_blocks]}")
        print(f"  break_blocks={[b.start_offset for b in r.break_blocks] if hasattr(r,'break_blocks') else 'N/A'}")
        lbfs = r.metadata.get('loop_body_full_set', set())
        print(f"  loop_body_full_set={[b.start_offset for b in lbfs]}")
        print(f"  natural_exit={r.natural_exit.start_offset if hasattr(r,'natural_exit') and r.natural_exit else None}")
        print(f"  natural_back_edge={r.natural_back_edge.start_offset if hasattr(r,'natural_back_edge') and r.natural_back_edge else None}")
        print(f"  for_iter_exit={r.metadata.get('for_iter_exit', None)}")
        if hasattr(r, 'for_iter_exit_block') and r.for_iter_exit_block:
            print(f"  for_iter_exit_block={r.for_iter_exit_block.start_offset}")
        else_blocks = r.metadata.get('else_blocks', None)
        print(f"  else_blocks={[b.start_offset for b in else_blocks] if else_blocks else None}")
