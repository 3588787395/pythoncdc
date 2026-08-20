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

# Print all blocks with their roles
region_analyzer = RegionAnalyzer(cfg)
region_analyzer.analyze()
region_analyzer._annotate_all_roles(region_analyzer.regions)

print("=== Block roles ===")
for offset, block in sorted(cfg.blocks.items()):
    role = region_analyzer.get_block_role(block)
    instrs = [(i.opname, i.arg, getattr(i, 'argval', None)) for i in block.instructions]
    print(f'  Block {block.id} (offset {block.start_offset}): role={role}, instrs={instrs}')
    print(f'    successors: {[s.id for s in block.successors]}')
    print(f'    conditional_successors: {len(block.conditional_successors)}')
    print(f'    immediate_post_dominator: {block.immediate_post_dominator.id if block.immediate_post_dominator else None}')

# Check the outer IfRegion
for region in region_analyzer.regions:
    if type(region).__name__ == 'IfRegion' and region.region_type.name == 'IF_THEN':
        print(f'\n=== Outer IfRegion (IF_THEN) ===')
        print(f'  entry: block {region.entry.id}')
        print(f'  then_blocks: {[b.id for b in region.then_blocks]}')
        print(f'  else_blocks: {[b.id for b in region.else_blocks]}')
        print(f'  merge_block: {region.merge_block.id if region.merge_block else None}')
        
        # Check condition block successors
        cond = region.condition_block
        print(f'  condition_block: {cond.id}')
        print(f'  cond successors: {[s.id for s in cond.successors]}')
        
        # then_succ and else_succ
        then_succ = None
        else_succ = None
        for s in cond.successors:
            if s in region.then_blocks:
                then_succ = s
            else:
                else_succ = s
        print(f'  then_succ: {then_succ.id if then_succ else None}')
        print(f'  else_succ: {else_succ.id if else_succ else None}')
        
        # Check else_succ role
        if else_succ:
            print(f'  else_succ role: {region_analyzer.get_block_role(else_succ)}')
            print(f'  else_succ instrs: {[(i.opname, i.arg) for i in else_succ.instructions]}')
