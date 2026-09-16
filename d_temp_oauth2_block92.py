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
import dis

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Show block 92 (the BoolOpRegion's merge_block)
for b in cfg.get_blocks_in_order():
    if b.start_offset == 92:
        print(f"Block 92:")
        for inst in b.instructions:
            print(f"  {inst.offset}: {inst.opname} {inst.argval}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")

# Also show the BoolOpRegion at entry=2
for r in regions:
    if isinstance(r, BoolOpRegion) and r.entry and r.entry.start_offset == 2:
        print(f"\nBoolOpRegion(entry=2):")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
        print(f"  merge_block={r.merge_block.start_offset}")
        print(f"  value_target={r.value_target}")
