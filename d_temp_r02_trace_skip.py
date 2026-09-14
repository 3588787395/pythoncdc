import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BoolOpRegion, BlockRole
from core.cfg.region_analyzer import FORWARD_CONDITIONAL_JUMP_OPS

import marshal, types

with open('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            result = find_code(const, name)
            if result:
                return result
    return None

tick = find_code(code, 'tick_worker_thread')

builder = CFGBuilder()
cfg = builder.build(tick)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Find the inner loop with header=50
inner_loop = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 50:
        inner_loop = region
        break

block_50 = cfg.get_block_by_offset(50)
last_instr = block_50.get_last_instruction()

print("=== Tracing _should_skip_block_for_if_region for block 50 ===")
print("block_50 last_instr: %s %s" % (last_instr.opname, last_instr.argval))
print("inner_loop condition_block: %s" % (inner_loop.condition_block.start_offset if inner_loop.condition_block else None))
print("inner_loop header_block: %s" % (inner_loop.header_block.start_offset if inner_loop.header_block else None))

# Check line 14630: block == block_region.condition_block
print("\nblock == condition_block: %s" % (block_50 == inner_loop.condition_block))
# Check line 14632: block == block_region.header_block
print("block == header_block: %s" % (block_50 == inner_loop.header_block))

# Line 14633: last_instr in BACKWARD_CONDITIONAL_JUMP_OPS
print("last_instr in BACKWARD: %s" % ('BACKWARD' in last_instr.opname))

# Line 14635: condition_block is None
print("condition_block is None: %s" % (inner_loop.condition_block is None))

# Line 14636: conditional_successors
cond_succs = list(block_50.conditional_successors)
print("\nconditional_successors: %d" % len(cond_succs))
for s in cond_succs:
    role = analyzer.get_block_role(s)
    print("  succ %d role=%s last=%s" % (s.start_offset, role, s.get_last_instruction().opname if s.get_last_instruction() else None))

# The key check: len(cond_succs) == 2?
# Block 50 has 3 successors: 168 (CONTINUE), 210 (LOOP_BODY), 1290 (EXCEPT_HANDLER)
# But conditional_successors might only return 2

if len(cond_succs) == 2:
    then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)
    print("\nthen_succ=%d else_succ=%d" % (then_succ.start_offset, else_succ.start_offset))
else:
    print("\nlen(cond_succs) != 2: %d" % len(cond_succs))
    print("This means block 50 is SKIPPED for IfRegion creation at line 14658!")
    print("The else branch at line 14657-14658 returns True (skip).")

# Now let's check what happens in the generation path
# Since block 50 is the header of a while-True loop with no condition_block,
# and it's not an IfRegion, it goes through _loop_handle_header

# Check what _loop_extract_self_loop_stmts produces for block 50
from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg, analyzer)
stmts = gen._loop_extract_self_loop_stmts(block_50)
print("\n_loop_extract_self_loop_stmts for block 50:")
for s in stmts:
    print("  %s" % s)
