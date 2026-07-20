"""Debug R6-06 except handler ternary - check handler_blocks."""
import sys
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator

src = """try:
    pass
except E:
    x = a if c else b
"""
code = compile(src, '<test>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== regions ===")
for r in analyzer.regions:
    print(f"Region: {type(r).__name__} {r.region_type}")
    if hasattr(r, 'except_handlers'):
        for idx, (exc_type, exc_name, handler_blocks) in enumerate(r.except_handlers):
            print(f"  Handler {idx}: exc_type={exc_type}, exc_name={exc_name}")
            print(f"    handler_blocks: {[b.start_offset for b in handler_blocks]}")
    if hasattr(r, 'handler_entry_blocks'):
        print(f"  handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}")

print()
print("=== generating AST ===")
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()
print("=== result ===")
print(result)
print()
decomp = CodeGenerator().generate(result)
print('=== decompiled ===')
print(decomp)
