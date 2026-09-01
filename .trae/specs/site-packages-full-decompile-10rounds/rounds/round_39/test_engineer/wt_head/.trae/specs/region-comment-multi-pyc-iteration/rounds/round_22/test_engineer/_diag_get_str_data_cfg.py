"""R22: diagnose get_str_data CFG and regions"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

PYC = r'f:/Downloads/pythoncdc-main/site-packages/fly/data/quotation.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    root = marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

# Find get_str_data
for c in collect(root, []):
    if c.co_name == 'get_str_data':
        code = c
        break

print(f'get_str_data: varnames={code.co_varnames[:10]}... co_consts_count={len(code.co_consts)}')

cfg = build_cfg(code)
blocks = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
print(f'CFG blocks: {len(blocks)}')

ra = RegionAnalyzer(cfg)
ra.analyze()

# Show regions
print(f'\nRegions ({len(ra.regions)}):')
for r in ra.regions:
    rtype = type(r).__name__
    entry = getattr(r, 'entry', None)
    entry_off = entry.start_offset if entry else None
    blocks_count = len(getattr(r, 'blocks', []))
    print(f'  {rtype} entry@{entry_off} blocks={blocks_count}')
    if rtype == 'TryExceptRegion':
        print(f'    try_offset_end={getattr(r, "try_offset_end", None)}')
        print(f'    has_else={getattr(r, "has_else", None)}')
        print(f'    else_blocks_count={len(getattr(r, "else_blocks", []))}')
