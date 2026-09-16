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

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Show all BoolOpRegions
for r in regions:
    if isinstance(r, BoolOpRegion):
        entry_off = r.entry.start_offset if r.entry else None
        blocks_off = [b.start_offset for b in r.blocks]
        op_chain = [(b.start_offset if hasattr(b,'start_offset') else b, op) for b, op in r.op_chain] if hasattr(r, 'op_chain') else []
        print(f"BoolOpRegion entry={entry_off}")
        print(f"  blocks={blocks_off}")
        print(f"  op_chain={op_chain}")
        print(f"  value_target={getattr(r, 'value_target', None)}")
        vt = getattr(r, 'value_target', None)
        if vt:
            print(f"  value_target type={type(vt).__name__}")
        merge = getattr(r, 'merge_block', None)
        if merge:
            print(f"  merge_block={merge.start_offset}")
