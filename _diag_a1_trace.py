import sys, os, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.code_generator import CodeGenerator

# A1: nested try with IndexError/AttributeError
source = 'try:\n    try:\n        pass\n    except IndexError:\n        pass\nexcept AttributeError:\n    pass'
code = compile(source, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

gen = RegionASTGenerator(cfg)

# Monkey-patch _generate_try to trace
original_generate_try = gen._generate_try.__func__

def traced_generate_try(self, region):
    print(f"\n>>> _generate_try called for region @ {id(region)}")
    print(f"    try_offset: {region.try_offset_start}-{region.try_offset_end}")
    print(f"    except_handlers: {region.except_handlers}")
    print(f"    handler_entry_blocks: {[b.start_offset for b in region.handler_entry_blocks]}")
    print(f"    parent: {type(region.parent).__name__ if region.parent else None}")
    result = original_generate_try(self, region)
    print(f"<<< _generate_try result: {result}")
    return result

import types as ty
gen._generate_try = ty.MethodType(traced_generate_try, gen)

result = gen.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print(f"\nFINAL DECOMPILED:\n{decompiled}")
