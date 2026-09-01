"""R21 trace post-processing of else_blocks"""
import marshal, sys, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion

# Monkey-patch to trace post-processing
_orig_identify = RegionAnalyzer._identify_try_except_regions
def _traced_identify(self):
    result = _orig_identify(self)
    print('\n=== Post _identify_try_except_regions ===')
    for r in result:
        if isinstance(r, TryExceptRegion):
            print(f'TryExceptRegion entry@{r.entry.start_offset}')
            print(f'  has_else={getattr(r, "has_else", None)}')
            print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
            enc = getattr(r, 'enclosing_try', None)
            if enc:
                print(f'  enclosing_try entry@{enc.entry.start_offset}')
                enc_else = enc.get_else_blocks_for_merge()
                print(f'  enclosing_else={[b.start_offset for b in enc_else]}')
    return result
RegionAnalyzer._identify_try_except_regions = _traced_identify

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
print(f'Analyzing _target (stream)')

cfg = build_cfg(t)
ra = RegionAnalyzer(cfg)
regions = ra.analyze()

# Final
for r in regions:
    if isinstance(r, TryExceptRegion):
        print(f'\nFinal: TryExceptRegion entry@{r.entry.start_offset}')
        print(f'  has_else={getattr(r, "has_else", None)}')
        print(f'  else_blocks={[b.start_offset for b in getattr(r, "else_blocks", [])]}')
