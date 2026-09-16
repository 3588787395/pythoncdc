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

print('block_to_region:')
for block, region in sorted(analyzer.block_to_region.items(), key=lambda x: x[0].start_offset):
    rtype = type(region).__name__
    entry_off = getattr(region, 'entry', None)
    if entry_off and hasattr(entry_off, 'start_offset'):
        entry_off = entry_off.start_offset
    print(f'  block {block.start_offset} -> {rtype} (entry={entry_off})')

print('\ngenerated_blocks after analyze:')
for b in sorted(analyzer.generated_blocks, key=lambda x: x.start_offset) if hasattr(analyzer, 'generated_blocks') else []:
    print(f'  {b.start_offset}')
