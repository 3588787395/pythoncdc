import sys, dis
sys.path.insert(0, '/workspace')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole, TryExceptRegion, IfRegion, LoopRegion
from core.cfg.code_generator import CodeGenerator

source = 'try:\n    for i in range(3):\n        if i < 1:\n            continue\nexcept:\n    y = 1'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Monkey-patch _build_statement to trace Break generation
orig_build = gen._build_statement.__func__
import types as ty

def traced_build(self, instrs):
    result = orig_build(self, instrs)
    if result and result.get('type') == 'Break':
        print(f"  _build_statement generated Break from: {[(i.opname, i.argval) for i in instrs]}")
    return result

gen._build_statement = ty.MethodType(traced_build, gen)

# Also trace _generate_try_body
orig_try_body = gen._generate_try_body.__func__

def traced_try_body(self, region):
    print(f"\n_generate_try_body called")
    result = orig_try_body(self, region)
    print(f"_generate_try_body result: {result}")
    return result

gen._generate_try_body = ty.MethodType(traced_try_body, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nDECOMPILED:\n{decompiled}")
