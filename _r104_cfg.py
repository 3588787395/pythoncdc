import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
import marshal, struct

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_09_multi_elif_break.pyc'
with open(path, 'rb') as f:
    f.read(4)
    f.read(4)
    f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

# Region analysis
region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

print("=== Regions ===")
for region in regions:
    print(f'  Region: type={type(region).__name__}')
    for attr in dir(region):
        if attr.startswith('_'):
            continue
        val = getattr(region, attr)
        if callable(val):
            continue
        if isinstance(val, (list, tuple, set)):
            val = list(val)
        if attr in ('region_type', 'entry', 'entry_block', 'entry_offset',
                     'condition_blocks', 'body_blocks', 'else_blocks',
                     'elif_conditions', 'elif_bodies', 'elif_final_else',
                     'loop_body', 'back_edge', 'loop_header',
                     'header', 'exit_blocks', 'orelse_blocks'):
            print(f'    {attr}: {val}')

# Check block 8 (offset 114) role
b114 = cfg.blocks[8]  # block 8 has offset 114
print(f'\n=== Block 8 (offset 114) ===')
print(f'  instructions: {[(i.opname, i.arg) for i in b114.instructions]}')
print(f'  successors: {b114.successors}')

# Check role
try:
    role = region_analyzer.get_block_role(b114)
    print(f'  region_analyzer role: {role}')
except Exception as e:
    print(f'  region_analyzer role error: {e}')

# Check BlockRole values
print(f'\n=== BlockRole values ===')
for attr in dir(BlockRole):
    if not attr.startswith('_'):
        print(f'  BlockRole.{attr} = {getattr(BlockRole, attr)}')
