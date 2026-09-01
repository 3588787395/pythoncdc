import sys
sys.path.insert(0, '.')
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
import marshal, types

def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def extract_func(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            r = extract_func(c, name)
            if r: return r
    return None

code = load_code('site-packages/IQEngine/utils/scheduler.pyc')
func = extract_func(code, 'on_before_trading')
cfg = CFGBuilder().build(func)
ra = RegionAnalyzer(cfg, func)
ra.analyze()

def print_region(r, indent=0):
    prefix = '  ' * indent
    binfo = str([b.id for b in r.blocks]) if hasattr(r, 'blocks') else 'N/A'
    print(f'{prefix}{type(r).__name__}: blocks={binfo}')
    if hasattr(r, 'sub_regions'):
        for sr in r.sub_regions:
            print_region(sr, indent + 1)
    if hasattr(r, 'handler') and r.handler:
        print(f'{prefix}  handler:')
        print_region(r.handler, indent + 2)
    if hasattr(r, 'orelse') and r.orelse:
        print(f'{prefix}  orelse:')
        print_region(r.orelse, indent + 2)
    if hasattr(r, 'body') and r.body:
        print(f'{prefix}  body:')
        print_region(r.body, indent + 2)
    if hasattr(r, 'merge_block') and r.merge_block:
        print(f'{prefix}  merge_block: block {r.merge_block.id}')

print('Top-level regions:')
for r in ra.regions:
    print_region(r)
