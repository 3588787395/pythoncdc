"""复现 adv13 ternary three or cond"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dis

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

src = "if (a if c else b) or (d if e else f) or (g if h else i):\n    pass"
code = compile(src, '<test>', 'exec')
print("=== Original bytecode ===")
for ins in dis.get_instructions(code):
    print(f"  {ins.offset:4} {ins.opname:30} {ins.argval}")

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
decompiled = code_gen.generate(result)
print("\n=== Decompiled ===")
print(decompiled)

recomp = compile(decompiled, '<dec>', 'exec')
print("\n=== Recompiled bytecode ===")
for ins in dis.get_instructions(recomp):
    print(f"  {ins.offset:4} {ins.opname:30} {ins.argval}")
