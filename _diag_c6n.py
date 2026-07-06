import sys
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator, FORWARD_CONDITIONAL_JUMP_OPS, BACKWARD_CONDITIONAL_JUMP_OPS
from core.cfg.region_analyzer import BlockRole
import types as ty

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Deep trace of _try_generate_conditional_break_or_continue
orig = gen._try_generate_conditional_break_or_continue.__func__

def traced(self, block):
    loop = self._current_loop
    if not loop:
        return orig(self, block)
    
    last_instr = block.get_last_instruction()
    if last_instr is None or (last_instr.opname not in FORWARD_CONDITIONAL_JUMP_OPS and last_instr.opname not in BACKWARD_CONDITIONAL_JUMP_OPS):
        return orig(self, block)
    
    print(f"\n_deep_trace block @ {block.start_offset}")
    
    # Trace the exact code path
    jump_target = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
    _ft_offset = last_instr.offset + 2
    if last_instr.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
        _ft_offset = None
    ft_block = None
    if _ft_offset is not None:
        _ft_block = self.cfg.get_block_by_offset(_ft_offset)
        if _ft_block is not None and _ft_block != jump_target:
            ft_block = _ft_block
    if ft_block is None:
        for s in block.successors:
            if s != jump_target:
                _s_role = self.region_analyzer.get_block_role(s)
                if _s_role not in (BlockRole.EXCEPT_HANDLER,):
                    ft_block = s
                    break
    
    print(f"  jump_target={jump_target.start_offset if jump_target else None}")
    print(f"  fall_through={ft_block.start_offset if ft_block else None}")
    
    # Call original
    result = orig(self, block)
    print(f"  result: {result}")
    return result

gen._try_generate_conditional_break_or_continue = ty.MethodType(traced, gen)

# Also trace _try_generate_conditional_break
orig2 = gen._try_generate_conditional_break.__func__

def traced2(self, block):
    print(f"\n_try_generate_conditional_break(block @ {block.start_offset})")
    result = orig2(self, block)
    print(f"  result: {result}")
    return result

gen._try_generate_conditional_break = ty.MethodType(traced2, gen)

result = gen.generate()
from core.cfg.code_generator import CodeGenerator
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
