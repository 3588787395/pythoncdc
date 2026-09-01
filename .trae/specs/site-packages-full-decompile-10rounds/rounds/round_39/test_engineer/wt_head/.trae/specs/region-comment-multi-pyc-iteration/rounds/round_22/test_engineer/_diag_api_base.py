"""R22: diagnose api_base.pyc else indentation error"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

# Find api_base.pyc
import json
with open(r'f:/Downloads/pythoncdc-main/pyc_index.json', 'r') as f:
    index = json.load(f)

pyc_path = None
for e in index:
    if 'api_base.pyc' in e.get('path', ''):
        pyc_path = e['path']
        break

print(f'Path: {pyc_path}')

with open(pyc_path, 'rb') as f:
    f.read(16)
    root = marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

# Find the function with the syntax error - likely a top-level function
for c in collect(root, []):
    if c.co_name == 'api_exec_filter':
        code = c
        break
else:
    # Try module-level code
    code = root

print(f'Target: {code.co_name} varnames={code.co_varnames[:5]}')

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
    last_op = last.opname if last else 'NONE'
    succs = sorted(s.start_offset for s in b.successors)
    print(f'  @{b.start_offset:4d} role={str(role):20s} last={last_op:30s} succs={succs}')

print(f'\nRegions ({len(ra.regions)}):')
for r in ra.regions:
    rtype = type(r).__name__
    entry = r.entry.start_offset if hasattr(r, 'entry') else '?'
    rblocks = [b.start_offset for b in getattr(r, 'blocks', [])]
    if rtype == 'IfRegion':
        then_b = [b.start_offset for b in getattr(r, 'then_blocks', [])]
        else_b = [b.start_offset for b in getattr(r, 'else_blocks', [])]
        print(f'  {rtype}@{entry} then={then_b} else={else_b}')
    else:
        print(f'  {rtype}@{entry} blocks={rblocks}')
