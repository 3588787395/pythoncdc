"""R21 trace _find_try_else_blocks calls"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

# Monkey-patch to trace
_orig_find = RegionAnalyzer._find_try_else_blocks
def _traced_find(self, try_region):
    result = _orig_find(self, try_region)
    entry_off = getattr(try_region.entry, 'start_offset', None)
    print(f'  _find_try_else_blocks(entry@{entry_off}) -> {[b.start_offset for b in result]}')
    return result
RegionAnalyzer._find_try_else_blocks = _traced_find

def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def collect(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            collect(c, out)
    return out

root = load_pyc(r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/logger/handlers.pyc')
targets = [c for c in collect(root, []) if c.co_name == '_target']
t = targets[-1]
print(f'Analyzing _target (stream) varnames={t.co_varnames}')

cfg = build_cfg(t)
ra = RegionAnalyzer(cfg)
print('Calling analyze()...')
regions = ra.analyze()

# Show final results
for r in regions:
    if type(r).__name__ == 'TryExceptRegion':
        print(f'\nTryExceptRegion entry@{r.entry.start_offset}')
        print(f'  has_else={getattr(r, "has_else", None)}')
        print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
