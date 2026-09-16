import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(co, name, parent_name=None):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                if parent_name is None or co.co_name == parent_name:
                    return c
            r = find_code(c, name, parent_name)
            if r: return r
    return None

co = find_code(code, 'post', 'OAuthCallbackHandler')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

gen = RegionASTGenerator(cfg, regions, analyzer)

# Trace the generate() step by step
# First, check the entry block
entry_block = cfg.entry_block
print(f"Entry block: {entry_block.start_offset}")
print(f"Generator entry: {analyzer.metadata.get('generator_entry_block', entry_block).start_offset}")

# Check top_level regions
top_level = [r for r in regions if r.parent is None]
print(f"\nTop-level regions:")
for r in top_level:
    rtype = type(r).__name__
    entry_off = r.entry.start_offset if r.entry else None
    blocks_off = [b.start_offset for b in r.blocks][:5]
    print(f"  {rtype}(entry={entry_off}) blocks={blocks_off}...")

# Now simulate the generate() entry block processing
gen_entry = analyzer.metadata.get('generator_entry_block', entry_block)
if gen_entry is not entry_block:
    gen.generated_blocks.add(entry_block)
    entry_block = gen_entry

print(f"\nAfter generator entry processing:")
print(f"  generated_blocks: {sorted(b.start_offset for b in gen.generated_blocks)}")
print(f"  entry_block to process: {entry_block.start_offset}")

# Check entry_region
entry_region = analyzer.get_entry_region_for_block(entry_block) or analyzer.get_region_for_block(entry_block)
print(f"  entry_region: {type(entry_region).__name__} entry={entry_region.entry.start_offset if entry_region and entry_region.entry else None}")

# The entry_region is a BoolOpRegion - check how generate() handles it
if isinstance(entry_region, BoolOpRegion):
    print("  BoolOpRegion as entry — pass (handled by region loop)")
elif isinstance(entry_region, IfRegion) and entry_region.condition_block == entry_block:
    print("  IfRegion with condition=entry — pass")
else:
    print("  Other entry region — _generate_block_statements")
    entry_ast = gen._generate_block_statements(entry_block)
    print(f"  entry_ast: {len(entry_ast)} items")
    for i, item in enumerate(entry_ast[:5]):
        if isinstance(item, dict):
            print(f"    [{i}] {item.get('type','?')}")

print(f"\nAfter entry block processing:")
print(f"  generated_blocks: {sorted(b.start_offset for b in gen.generated_blocks)}")

# Now run the full generate to see what happens
gen2 = RegionASTGenerator(cfg, regions, analyzer)
result = gen2.generate()
print(f"\nFull generate result:")
if isinstance(result, dict):
    body = result.get('body', [])
    print(f"  body_len={len(body)}")
    for i, b in enumerate(body[:5]):
        if isinstance(b, dict):
            print(f"    body[{i}]: {b.get('type','?')}")
