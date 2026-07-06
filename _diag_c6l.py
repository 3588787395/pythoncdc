import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, NOISE_OPS, CONDITIONAL_JUMP_OPS, SHORT_CIRCUIT_JUMP_OPS
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
    if loop:
        print(f"\n_try_generate_conditional_break_or_continue(block @ {block.start_offset})")
        print(f"  loop: header={loop.header_block.start_offset if loop.header_block else None}")
        print(f"  loop: condition={loop.condition_block.start_offset if loop.condition_block else None}")
        print(f"  loop: back_edge={loop.back_edge_block.start_offset if loop.back_edge_block else None}")
        print(f"  loop: body_blocks={[b.start_offset for b in (loop.body_blocks or [])]}")
        
        last_instr = block.get_last_instruction()
        jump_target = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
        _ft_offset = last_instr.offset + 2
        ft_block = self.cfg.get_block_by_offset(_ft_offset)
        print(f"  jump_target={jump_target.start_offset if jump_target else None}")
        print(f"  fall_through={ft_block.start_offset if ft_block else None}")
        
        # Check _is_continue_like for each successor
        for succ in [jump_target, ft_block]:
            if succ is None:
                continue
            role = self.region_analyzer.get_block_role(succ)
            last = succ.get_last_instruction()
            print(f"  succ {succ.start_offset}: role={role.name}")
            if last and last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                target = self.cfg.get_block_by_offset(last.argval)
                print(f"    JUMP_BACKWARD target={target.start_offset if target else None}, loop.header={loop.header_block.start_offset if loop.header_block else None}")
                if target == loop.header_block:
                    print(f"    → continue-like!")
    
    result = orig(self, block)
    if loop:
        print(f"  result: {result}")
    return result

gen._try_generate_conditional_break_or_continue = ty.MethodType(traced, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
