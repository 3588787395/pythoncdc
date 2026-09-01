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

# Check block_to_region for block 16
b16 = cfg.blocks[16]
owner = ra.block_to_region.get(b16)
print(f"Block 16 owner: {type(owner).__name__ if owner else None}")

# Check if block 16 is in any region's blocks
for r in ra.regions:
    if b16 in r.blocks:
        print(f"Block 16 is in {type(r).__name__} blocks!")
        
# Check all blocks and their ownership
for bid in sorted(cfg.blocks.keys()):
    block = cfg.blocks[bid]
    owner = ra.block_to_region.get(block)
    print(f"Block {bid}: owner={type(owner).__name__ if owner else 'UNOWNED'}")
