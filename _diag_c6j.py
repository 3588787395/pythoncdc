import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS
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
    last_instr = block.get_last_instruction()
    print(f"\n_try_generate_conditional_break_or_continue(block @ {block.start_offset})")
    if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
        jump_target = self.cfg.get_block_by_offset(last_instr.argval)
        _ft_offset = last_instr.offset + 2
        ft_block = self.cfg.get_block_by_offset(_ft_offset)
        print(f"  jump_target={jump_target.start_offset if jump_target else None}")
        print(f"  ft_offset={_ft_offset}, ft_block={ft_block.start_offset if ft_block else None}")
        print(f"  block.successors={[s.start_offset for s in block.successors]}")
    
    result = orig(self, block)
    print(f"  result: {result}")
    return result

gen._try_generate_conditional_break_or_continue = ty.MethodType(traced, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
