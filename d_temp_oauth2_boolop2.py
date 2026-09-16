import sys, types
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
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

# Monkey-patch _generate_boolop to trace when it processes block 140
orig_gen_boolop = RegionASTGenerator._generate_boolop

def traced_gen_boolop(self, region, skip_store_targets=None):
    # Check if this BoolOpRegion would process block 140
    if region.entry and hasattr(region, 'blocks'):
        blocks_off = [b.start_offset for b in region.blocks]
        if 140 in blocks_off:
            print(f"\n!!! BoolOpRegion(entry={region.entry.start_offset}) contains block 140!", file=sys.stderr)
            print(f"  blocks={blocks_off}", file=sys.stderr)
    
    # Also check the _then_blk_r89 variable
    result = orig_gen_boolop(self, region, skip_store_targets=skip_store_targets)
    return result

RegionASTGenerator._generate_boolop = traced_gen_boolop

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)
result = gen.generate()

body = result.get('body', [])
print(f"\nFunction body: {len(body)} items")
