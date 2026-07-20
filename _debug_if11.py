"""Debug if11ifor to see decompiled output."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

source = """if a or b:
    pass"""

from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

code = compile(source, '<test>', 'exec')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

analyzer = RegionAnalyzer(cfg)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()

code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print("=== DECOMPILED ===")
print(repr(decompiled))
print(decompiled)
print()

import dis
print("=== ORIGINAL BYTECODE ===")
dis.dis(code)
print()
print("=== RECOMPILED BYTECODE ===")
recompiled = compile(decompiled, '<test>', 'exec')
dis.dis(recompiled)
