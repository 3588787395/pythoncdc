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

# Now re-analyze and check the WithRegion
ra.analyze()

for r in ra.regions:
    if type(r).__name__ == 'WithRegion' and 1 in [b.id for b in r.blocks]:
        print(f"Outer WithRegion:")
        print(f"  blocks: {sorted([b.id for b in r.blocks])}")
        print(f"  cleanup_blocks: {sorted([b.id for b in r.cleanup_blocks])}")
        print(f"  exception_blocks: {sorted([b.id for b in r.exception_blocks])}")
        print(f"  with_blocks: {sorted([b.id for b in r.with_blocks])}")
        print(f"  exit_block: {r.exit_block.id if r.exit_block else None}")
        print(f"  exit_via_jump: {r.exit_via_jump}")
