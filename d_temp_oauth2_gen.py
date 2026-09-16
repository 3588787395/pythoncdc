import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_analyzer import IfRegion
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

# Now let's manually test the AST generator on this function
gen = RegionASTGenerator(cfg, regions, analyzer)

# Find the outer IfRegion at entry=140
outer_if = None
inner_if = None
for r in regions:
    if isinstance(r, IfRegion):
        if r.entry and r.entry.start_offset == 140:
            outer_if = r
        elif r.entry and r.entry.start_offset == 210:
            inner_if = r

print("Outer IfRegion (entry=140):")
print(f"  then_blocks={[b.start_offset for b in outer_if.then_blocks]}")
print(f"  else_blocks={[b.start_offset for b in outer_if.else_blocks]}")
print(f"  merge_block={outer_if.merge_block.start_offset if outer_if.merge_block else None}")

print("\nInner IfRegion (entry=210):")
print(f"  then_blocks={[b.start_offset for b in inner_if.then_blocks]}")
print(f"  else_blocks={[b.start_offset for b in inner_if.else_blocks]}")
print(f"  merge_block={inner_if.merge_block.start_offset if inner_if.merge_block else None}")

# Generate just the inner IfRegion and see what we get
result = gen._generate_if(inner_if)
print("\nGenerated inner IfRegion result:")
import json
def truncate(d, depth=0):
    if isinstance(d, dict):
        if depth > 3:
            return '{...}'
        return {k: truncate(v, depth+1) for k, v in d.items()}
    if isinstance(d, list):
        if len(d) > 5:
            return [truncate(v, depth+1) for v in d[:5]] + ['...']
        return [truncate(v, depth+1) for v in d]
    return d
print(json.dumps(truncate(result), indent=2, default=str))
