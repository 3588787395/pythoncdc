"""Trace how Block@602 and Block@532 are processed in AST generation."""
import sys, dis, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
from core.cfg.region_ast_generator import RegionASTGenerator

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

# Check block regions
b532 = cfg.get_block_by_offset(532)
b602 = cfg.get_block_by_offset(602)

print(f"Block@532 role: {analyzer.get_block_role(b532)}")
print(f"Block@532 region: {analyzer.get_region_for_block(b532)}")
print(f"Block@532 entry region: {analyzer.get_entry_region_for_block(b532)}")
print(f"Block@602 role: {analyzer.get_block_role(b602)}")
print(f"Block@602 region: {analyzer.get_region_for_block(b602)}")
print(f"Block@602 entry region: {analyzer.get_entry_region_for_block(b602)}")

# Check which regions contain these blocks
for r in analyzer.regions:
    blocks_set = set(getattr(r, 'blocks', []))
    if b532 in blocks_set:
        print(f"Block@532 in {type(r).__name__} blocks")
    if b602 in blocks_set:
        print(f"Block@602 in {type(r).__name__} blocks")
    if hasattr(r, 'try_blocks'):
        try_set = set(r.try_blocks)
        if b532 in try_set:
            print(f"Block@532 in {type(r).__name__} try_blocks")
    if hasattr(r, 'else_blocks'):
        else_set = set(r.else_blocks) if r.else_blocks else set()
        if b532 in else_set or b602 in else_set:
            print(f"Block@532/602 in {type(r).__name__} else_blocks")
    if hasattr(r, 'handler_entry_blocks'):
        handler_set = set(r.handler_entry_blocks)
        if b532 in handler_set or b602 in handler_set:
            print(f"Block@532/602 in {type(r).__name__} handler_entry_blocks")
    if hasattr(r, 'body_blocks'):
        body_set = set(r.body_blocks)
        if b532 in body_set or b602 in body_set:
            print(f"Block@532/602 in {type(r).__name__} body_blocks")

# Check block_to_region mapping
b2r = analyzer.block_to_region if hasattr(analyzer, 'block_to_region') else {}
for b in [b532, b602]:
    r = b2r.get(b, None) if isinstance(b2r, dict) else None
    print(f"Block@{b.start_offset} block_to_region: {type(r).__name__ if r else None}")
