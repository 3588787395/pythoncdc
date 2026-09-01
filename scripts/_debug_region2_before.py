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
    binfo = str(sorted([b.id for b in r.blocks])) if hasattr(r, 'blocks') else 'N/A'
    print(f'{prefix}{type(r).__name__}: blocks={binfo}')
    for attr in ['body', 'orelse', 'handler', 'context_expr', 'merge_block']:
        val = getattr(r, attr, None)
        if val is not None:
            if hasattr(val, 'blocks'):
                print(f'{prefix}  {attr}: {type(val).__name__} blocks={sorted([b.id for b in val.blocks])}')
            elif hasattr(val, 'id'):
                print(f'{prefix}  {attr}: block {val.id}')
            else:
                print(f'{prefix}  {attr}: {val}')
    if hasattr(r, 'sub_regions'):
        for sr in r.sub_regions:
            print_region(sr, indent + 1)
    for attr in ['entry', 'exit', 'continue_block', 'break_block']:
        val = getattr(r, attr, None)
        if val is not None:
            if hasattr(val, 'id'):
                print(f'{prefix}  {attr}: block {val.id}')

for r in ra.regions:
    print_region(r)
    print('---')
