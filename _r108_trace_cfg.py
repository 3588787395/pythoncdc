"""Trace validate_data CFG blocks, roles, and region structure."""
import sys, dis, marshal, struct
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

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

print("=== validate_data CFG Blocks ===")
# cfg.blocks might be a dict
blocks = cfg.blocks
if isinstance(blocks, dict):
    blocks = list(blocks.values())
for block in sorted(blocks, key=lambda b: b.start_offset):
    role = analyzer.get_block_role(block)
    region = analyzer.get_region_for_block(block)
    last = block.get_last_instruction()
    last_str = f"{last.opname} {last.argval}" if last else "None"
    succs = [s.start_offset for s in block.successors]
    instrs = [(i.offset, i.opname, i.argval) for i in block.instructions]
    print(f"  Block@{block.start_offset}: role={role}, region={type(region).__name__ if region else None}, last={last_str}, succs={succs}")
    for ins in instrs:
        print(f"    {ins}")
    print()

print("\n=== Region Tree ===")
def print_region(r, indent=0):
    sp = "  " * indent
    print(f"{sp}{type(r).__name__}: entry={r.entry_block.start_offset if hasattr(r,'entry_block') and r.entry_block else 'N/A'}")
    blocks = getattr(r, 'blocks', [])
    if blocks:
        print(f"{sp}  blocks={[b.start_offset if hasattr(b,'start_offset') else b for b in blocks]}")
    for child in getattr(r, 'children', []):
        print_region(child, indent + 1)

for root in analyzer.root_regions:
    print_region(root)
