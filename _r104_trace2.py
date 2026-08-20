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

# Monkey-patch _identify_conditional_regions to check block 9 role
original_method = region_analyzer._identify_conditional_regions
def traced_method(*args, **kwargs):
    block9 = cfg.blocks[9]
    role = region_analyzer.get_block_role(block9)
    print(f"Before _identify_conditional_regions: block 9 role = {role}")
    result = original_method(*args, **kwargs)
    role = region_analyzer.get_block_role(block9)
    print(f"After _identify_conditional_regions: block 9 role = {role}")
    
    # Check the IfRegion that was created
    for r in result:
        if type(r).__name__ == 'IfRegion' and r.region_type.name == 'IF_THEN':
            print(f"  IfRegion (IF_THEN): entry={r.entry.id}, else_blocks={[b.id for b in r.else_blocks]}, merge={r.merge_block.id if r.merge_block else None}")
    return result

region_analyzer._identify_conditional_regions = traced_method

region_analyzer.analyze()
