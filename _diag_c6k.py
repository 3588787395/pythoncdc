import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS, NOISE_OPS, CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS
from core.cfg.region_analyzer import BlockRole, LoopRegion
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Check roles
block42 = cfg.get_block_by_offset(42)
block44 = cfg.get_block_by_offset(44)
print(f"Block 42 role: {gen.region_analyzer.get_block_role(block42).name}")
print(f"Block 44 role: {gen.region_analyzer.get_block_role(block44).name}")

# Find the loop
loop = None
for r in gen.region_analyzer.regions:
    if isinstance(r, LoopRegion):
        loop = r
        print(f"Loop: header={r.header_block.start_offset}, back_edge={r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"  body_blocks={[b.start_offset for b in (r.body_blocks or [])]}")
        break

# Manually check _is_continue_like and _is_break_like for blocks 42 and 44
if loop:
    loop_body_set = loop.metadata.get('loop_body_full_set', set(loop.body_blocks) | {loop.header_block})
    if loop.condition_block:
        loop_body_set.add(loop.condition_block)
    
    for block in [block42, block44]:
        role = gen.region_analyzer.get_block_role(block)
        print(f"\nBlock {block.start_offset}:")
        print(f"  role: {role.name}")
        print(f"  in loop_body_set: {block in loop_body_set}")
        print(f"  last_instr: {block.get_last_instruction().opname if block.get_last_instruction() else None}")
        
        # _is_continue_like
        is_continue = False
        if role == BlockRole.LOOP_BACK_EDGE:
            _lnj = [i for i in block.instructions
                   if i.opname not in NOISE_OPS
                   and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                   and i.opname not in CONDITIONAL_JUMP_OPS
                   and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
            if _lnj:
                print(f"  LOOP_BACK_EDGE with meaningful instrs: {[(i.opname, i.argval) for i in _lnj]}")
                is_continue = False
            else:
                is_continue = True
        if role in (BlockRole.PURE_CONTINUE, BlockRole.LOOP_BACK_EDGE):
            is_continue = True
        if block == loop.back_edge_block:
            is_continue = True
        last = block.get_last_instruction()
        if last and last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            target = cfg.get_block_by_offset(last.argval)
            if target == loop.header_block:
                is_continue = True
        print(f"  _is_continue_like: {is_continue}")
        
        # _is_break_like
        is_break = False
        if role in (BlockRole.BREAK, BlockRole.PURE_BREAK, BlockRole.RETURN, BlockRole.RETURN_NONE):
            is_break = True
        if block not in loop_body_set:
            last_instr = block.get_last_instruction()
            if last_instr:
                if last_instr.opname == 'RETURN_CONST' and last_instr.argval is not None:
                    is_break = False
                elif last_instr.opname == 'RETURN_VALUE':
                    for _ri in reversed(block.instructions):
                        if _ri == last_instr:
                            continue
                        if _ri.opname == 'LOAD_FAST' or (_ri.opname == 'LOAD_CONST' and _ri.argval is not None):
                            is_break = False
                            break
                        if _ri.opname not in ('NOP', 'CACHE', 'POP_TOP'):
                            break
                    else:
                        is_break = True
                else:
                    is_break = True
            else:
                is_break = True
        print(f"  _is_break_like: {is_break}")
