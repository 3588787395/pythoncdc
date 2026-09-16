import sys, types, os
os.environ['R7_DEBUG_IFGEN'] = '1'
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

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
builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
gen = RegionASTGenerator(cfg, regions, analyzer)

# Find the outer IfRegion
outer_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 140:
        outer_if = r
        break

# Check what _process_if_blocks does with then_blocks
print("=== Outer IfRegion then_blocks ===")
print([b.start_offset for b in outer_if.then_blocks])

# Find inner IfRegion
inner_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 210:
        inner_if = r
        break

print("\n=== Inner IfRegion ===")
print(f"entry={inner_if.entry.start_offset}")
print(f"blocks={[b.start_offset for b in inner_if.blocks]}")
print(f"then_blocks={[b.start_offset for b in inner_if.then_blocks]}")
print(f"else_blocks={[b.start_offset for b in inner_if.else_blocks]}")

# Check if inner's blocks are all in outer's then_blocks
then_block_set = set(outer_if.then_blocks)
all_in = all(b in then_block_set for b in inner_if.blocks)
print(f"\nAll inner blocks in outer then_blocks: {all_in}")

# Check get_region_for_block for block 210
region_for_210 = analyzer.get_region_for_block(inner_if.entry)
print(f"get_region_for_block(210): {type(region_for_210).__name__} entry={region_for_210.entry.start_offset if hasattr(region_for_210, 'entry') and region_for_210.entry else None}")

# Check get_entry_region_for_block
if hasattr(analyzer, 'get_entry_region_for_block'):
    entry_region = analyzer.get_entry_region_for_block(inner_if.entry)
    print(f"get_entry_region_for_block(210): {type(entry_region).__name__ if entry_region else None}")

# Now generate the outer IfRegion and check the result
print("\n=== Generating outer IfRegion ===")
result = gen._generate_if(outer_if)
print(f"Result type: {type(result)}")
print(f"Result length: {len(result) if isinstance(result, list) else 1}")

# Show the If statement structure
for i, item in enumerate(result if isinstance(result, list) else [result]):
    if isinstance(item, dict):
        t = item.get('type', '?')
        if t == 'If':
            body = item.get('body', [])
            orelse = item.get('orelse', [])
            test = item.get('test', {})
            print(f"  Item {i}: If test={test.get('type', '?')} body_len={len(body)} orelse_len={len(orelse)}")
            for j, stmt in enumerate(body):
                if isinstance(stmt, dict):
                    print(f"    body[{j}]: {stmt.get('type', '?')}")
        else:
            print(f"  Item {i}: {t}")
