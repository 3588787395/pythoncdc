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
print("Found post:", co.co_name, co.co_varnames[:5])

builder = CFGBuilder()
cfg = builder.build(co)

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("Regions:", len(regions))
for r in regions:
    rtype = type(r).__name__
    entry = getattr(r, 'entry', None)
    if entry:
        entry_off = getattr(entry, 'start_offset', entry)
    else:
        entry_off = '?'
    blocks = getattr(r, 'blocks', [])
    if blocks:
        block_offsets = [getattr(b, 'start_offset', b) for b in blocks]
    else:
        block_offsets = []
    print(f"  {rtype} entry={entry_off} blocks={block_offsets}")
    # If it's an IfRegion, show more details
    if rtype == 'IfRegion':
        cond = getattr(r, 'condition_blocks', [])
        true_br = getattr(r, 'true_blocks', [])
        false_br = getattr(r, 'false_blocks', [])
        print(f"    condition={[getattr(b,'start_offset',b) for b in cond]}")
        print(f"    true={[getattr(b,'start_offset',b) for b in true_br]}")
        print(f"    false={[getattr(b,'start_offset',b) for b in false_br]}")
