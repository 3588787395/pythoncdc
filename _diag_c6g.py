import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Monkey-patch all methods that could generate Break
import types as ty

orig_cb = gen._try_generate_conditional_break.__func__
def traced_cb(self, block):
    result = orig_cb(self, block)
    if result:
        print(f"  _try_generate_conditional_break(block @ {block.start_offset}): {result}")
    return result
gen._try_generate_conditional_break = ty.MethodType(traced_cb, gen)

orig_cbc = gen._try_generate_conditional_break_or_continue.__func__
def traced_cbc(self, block):
    result = orig_cbc(self, block)
    if result:
        print(f"  _try_generate_conditional_break_or_continue(block @ {block.start_offset}): {result}")
    return result
gen._try_generate_conditional_break_or_continue = ty.MethodType(traced_cbc, gen)

orig_pib = gen._process_if_blocks.__func__
def traced_pib(self, blocks, region, branch='then'):
    print(f"\n  _process_if_blocks(branch={branch}, blocks={[b.start_offset for b in blocks]})")
    result = orig_pib(self, blocks, region, branch)
    print(f"  _process_if_blocks result: {result}")
    return result
gen._process_if_blocks = ty.MethodType(traced_pib, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
