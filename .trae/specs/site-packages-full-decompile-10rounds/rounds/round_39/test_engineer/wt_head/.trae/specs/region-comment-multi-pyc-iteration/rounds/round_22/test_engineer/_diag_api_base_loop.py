"""R22: diagnose api_base.pyc decorate_api_exc while-else"""
import marshal, sys, types, json
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion

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

print(f'decorate_api_exc varnames={code.co_varnames}')

cfg = build_cfg(code)
ra = RegionAnalyzer(cfg)
ra.analyze()

blocks = sorted(
    (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)),
    key=lambda x: x.start_offset
)
print(f'\nBlocks ({len(blocks)}):')
for b in blocks:
    role = ra.get_block_role(b)
    last = b.get_last_instruction()
    succs = sorted(s.start_offset for s in b.successors)
    print(f'  @{b.start_offset:4d} role={str(role):20s} last={last.opname if last else "NONE":20s} succs={succs}')

print(f'\nRegions:')
for r in ra.regions:
    rtype = type(r).__name__
    entry = r.entry.start_offset if hasattr(r, 'entry') else '?'
    if isinstance(r, LoopRegion):
        has_break = getattr(r, 'has_break', False)
        else_blocks = [b.start_offset for b in getattr(r, 'else_blocks', [])]
        body_blocks = [b.start_offset for b in getattr(r, 'body_blocks', [])]
        print(f'  {rtype}@{entry} has_break={has_break} else={else_blocks} body={body_blocks}')
    else:
        rblocks = [b.start_offset for b in getattr(r, 'blocks', [])]
        print(f'  {rtype}@{entry} blocks={rblocks}')
