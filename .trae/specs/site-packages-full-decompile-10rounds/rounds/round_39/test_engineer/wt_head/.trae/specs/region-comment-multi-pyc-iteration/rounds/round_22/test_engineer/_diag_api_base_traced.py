"""R22: trace _find_loop_else for api_base.pyc while-else"""
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

cfg = build_cfg(code)
ra = RegionAnalyzer(cfg)

_orig_find = ra._find_loop_else.__func__
def _traced_find(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
    result = _orig_find(self, header, loop_body, loop_type, for_iter_exit, condition_block)
    else_blocks, natural_exit = result
    print(f'_find_loop_else: loop_type={loop_type}')
    print(f'  header={header.start_offset} for_iter_exit={for_iter_exit.start_offset if for_iter_exit else None}')
    print(f'  condition_block={condition_block.start_offset if condition_block else None}')
    print(f'  else_blocks={[b.start_offset for b in else_blocks] if else_blocks else None}')
    print(f'  natural_exit={natural_exit.start_offset if natural_exit else None}')
    return result

import types as _types
ra._find_loop_else = _types.MethodType(_traced_find, ra)

ra.analyze()

for r in ra.regions:
    if isinstance(r, LoopRegion):
        print(f'\nLoopRegion: has_break={r.has_break} else={[b.start_offset for b in r.else_blocks]} body={[b.start_offset for b in r.body_blocks]}')
