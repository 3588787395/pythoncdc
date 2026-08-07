"""R22: check _check_block_has_trailing_return_none for block@104"""
import marshal, sys, types, json, dis
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

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

blocks = sorted(
    (list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)),
    key=lambda x: x.start_offset
)

for b in blocks:
    print(f'Block@{b.start_offset}:')
    for inst in b.instructions:
        print(f'  {inst.offset:4d} {inst.opname:30s} {inst.arg if inst.arg is not None else ""}')
    last = b.get_last_instruction()
    if last:
        print(f'  last={last.opname} has_trailing_return_none={ra._check_block_has_trailing_return_none(b)}')
    succs = sorted(s.start_offset for s in b.successors)
    print(f'  succs={succs}')
    print()
