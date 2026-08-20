import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_09_multi_elif_break.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)

# Monkey-patch to trace block 9 role changes
original_assign = region_analyzer._assign_region_role
def traced_assign(offset, role):
    if offset == 116:
        print(f"  _assign_region_role(116, {role})")
    original_assign(offset, role)
region_analyzer._assign_region_role = traced_assign

# Also trace direct block_roles assignments
original_roles = region_analyzer.block_roles

class TracedDict(dict):
    def __setitem__(self, key, value):
        if key == 116:
            import traceback
            stack = ''.join(traceback.format_stack()[-3:-1]).strip()
            print(f"  block_roles[116] = {value} (from: {stack[:100]})")
        super().__setitem__(key, value)

region_analyzer.block_roles = TracedDict(original_roles)

region_analyzer.analyze()

# Final check
block9 = cfg.blocks[9]
print(f"\nFinal block 9 role: {region_analyzer.get_block_role(block9)}")
