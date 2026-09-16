import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find OAuthCallbackHandler.post
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
print("Found post:", co.co_name, co.co_varnames[:5])

builder = CFGBuilder()
cfg = builder.build(co)
print("Blocks:", len(cfg.blocks))
for b in cfg.get_blocks_in_order():
    print(f"\nBlock {b.id} start={b.start_offset} end={b.end_offset}:")
    for inst in b.instructions:
        print(f"  {inst.offset:4d} {inst.opname:30s} {inst.arg if inst.arg is not None else ''}")
    print(f"  successors: {[s.start_offset for s in b.successors]}")
    print(f"  exception_successors: {[s.start_offset for s in b.exception_successors]}")
