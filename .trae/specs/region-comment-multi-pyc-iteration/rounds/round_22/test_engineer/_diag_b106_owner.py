"""R22: check block@106 region ownership in api_base"""
import marshal, sys, types, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator

with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

with open(pyc_path, 'rb') as f:
    f.read(16)
    root = marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

for c in collect(root, []):
    if c.co_name == 'decorate_api_exc':
        code = c
        break

cfg = build_cfg(code)
ra = RegionAnalyzer(cfg)
ra.analyze()

# Check block@106 region ownership
blocks = sorted(
    (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)),
    key=lambda x: x.start_offset
)
b106 = [b for b in blocks if b.start_offset == 106][0]

owner = ra.block_to_region.get(b106)
print(f'block@106 owner: {type(owner).__name__ if owner else "UNOWNED"}')
if owner and hasattr(owner, 'entry'):
    print(f'  owner entry: {owner.entry.start_offset}')

for r in ra.regions:
    if b106 in r.blocks:
        rtype = type(r).__name__
        entry = r.entry.start_offset if hasattr(r, 'entry') else '?'
        print(f'  block@106 in {rtype}@{entry}')

# Check if block@106 is in LoopRegion else_blocks
for r in ra.regions:
    if isinstance(r, LoopRegion):
        print(f'\nLoopRegion@{r.entry.start_offset}:')
        print(f'  body={[b.start_offset for b in r.body_blocks]}')
        print(f'  else={[b.start_offset for b in r.else_blocks]}')
        print(f'  blocks={[b.start_offset for b in r.blocks]}')
        print(f'  has_break={r.has_break}')
