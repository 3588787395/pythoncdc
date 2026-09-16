import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

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

for r in regions:
    rtype = type(r).__name__
    if rtype == 'IfRegion':
        entry = getattr(r, 'entry', None)
        entry_off = getattr(entry, 'start_offset', entry) if entry else '?'
        print(f"IfRegion entry={entry_off}")
        print(f"  condition_block={getattr(r, 'condition_block', None)}")
        if r.condition_block:
            print(f"    start_offset={r.condition_block.start_offset}")
        print(f"  then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  merge_block={getattr(r, 'merge_block', None)}")
        if r.merge_block:
            print(f"    start_offset={r.merge_block.start_offset}")
        print(f"  blocks={[b.start_offset for b in r.blocks]}")
