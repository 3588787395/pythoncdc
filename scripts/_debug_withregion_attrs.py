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

# Find the outer WithRegion (blocks include 1, which is the entry with BEFORE_WITH)
for r in ra.regions:
    if type(r).__name__ == 'WithRegion' and 1 in [b.id for b in r.blocks]:
        print(f'Outer WithRegion attributes:')
        for attr in sorted(dir(r)):
            if not attr.startswith('_'):
                val = getattr(r, attr, None)
                if val is not None and not callable(val):
                    if hasattr(val, 'id'):
                        print(f'  {attr}: block {val.id}')
                    elif isinstance(val, list) and len(val) > 0 and hasattr(val[0], 'id'):
                        print(f'  {attr}: blocks {[b.id for b in val]}')
                    elif isinstance(val, list) and len(val) > 0 and hasattr(val[0], 'blocks'):
                        print(f'  {attr}: sub-regions with blocks {[sorted([b.id for b in sr.blocks]) for sr in val]}')
                    else:
                        try:
                            s = str(val)
                            if len(s) < 200:
                                print(f'  {attr}: {s}')
                        except:
                            pass
