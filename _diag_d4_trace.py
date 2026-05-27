import sys, types, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.code_generator import CodeGenerator

source = 'def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default'
code = compile(source, '<test>', 'exec')
f_code = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(f_code)

gen = RegionASTGenerator(cfg, recursive=True, parent_code=f_code)

# Monkey-patch _generate_handler_body_statements to trace
orig = gen._generate_handler_body_statements.__func__

def traced(self, block):
    print(f"  _generate_handler_body_statements(block @ {block.start_offset})")
    print(f"    instructions: {[(i.opname, i.argval) for i in block.instructions]}")
    result = orig(self, block)
    print(f"    result: {result}")
    return result

import types as ty
gen._generate_handler_body_statements = ty.MethodType(traced, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
