import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, NOISE_OPS, CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS, FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS
from core.cfg.region_analyzer import BlockRole, LoopRegion
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Monkey-patch _try_generate_conditional_break_or_continue to trace
import types as ty

orig = gen._try_generate_conditional_break_or_continue.__func__

def traced(self, block):
    loop = self._current_loop
    if not loop:
        return orig(self, block)
    
    last_instr = block.get_last_instruction()
    if last_instr is None or last_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS and last_instr.opname not in BACKWARD_CONDITIONAL_JUMP_OPS:
        return orig(self, block)
    
    print(f"\n_try_generate_conditional_break_or_continue(block @ {block.start_offset})")
    
    jump_target = self.cfg.get_block_by_offset(last_instr.argval)
    _ft_offset = last_instr.offset + 2
    ft_block = self.cfg.get_block_by_offset(_ft_offset) if _ft_offset else None
    
    # Manually run _is_continue_like for each successor
    for succ, is_jump in [(jump_target, True), (ft_block, False)]:
        if succ is None:
            continue
        role = self.region_analyzer.get_block_role(succ)
        is_continue = False
        if role in (BlockRole.PURE_CONTINUE, BlockRole.LOOP_BACK_EDGE):
            is_continue = True
        if succ == loop.back_edge_block:
            is_continue = True
        last = succ.get_last_instruction()
        if last and last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            target = self.cfg.get_block_by_offset(last.argval)
            if target == loop.header_block:
                is_continue = True
        print(f"  succ {succ.start_offset} (is_jump={is_jump}): role={role.name}, is_continue_like={is_continue}")
    
    result = orig(self, block)
    print(f"  result: {result}")
    return result

gen._try_generate_conditional_break_or_continue = ty.MethodType(traced, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
