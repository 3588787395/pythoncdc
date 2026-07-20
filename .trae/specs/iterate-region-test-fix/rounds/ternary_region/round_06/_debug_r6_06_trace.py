"""Debug R6-06 — trace what adds TernaryRegion to _generated_regions."""
import sys
import traceback
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, TernaryRegion
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

gen = RegionASTGenerator(cfg)

# Traced set that prints stack trace when a TernaryRegion id is added.
class TracedSet(set):
    def __init__(self, owner):
        super().__init__()
        self._owner = owner
    def add(self, x):
        # Look up the region by id in the owner's region_analyzer.regions
        try:
            for r in self._owner.region_analyzer.regions:
                if id(r) == x and isinstance(r, TernaryRegion):
                    print(f"\n*** _generated_regions.add(TernaryRegion id={x}, entry={r.entry.start_offset if r.entry else None}) ***", file=sys.stderr)
                    traceback.print_stack(file=sys.stderr)
                    print("*** end trace ***\n", file=sys.stderr)
                    break
        except Exception:
            pass
        super().add(x)

gen._generated_regions = TracedSet(gen)

print("\n=== generating AST ===", file=sys.stderr)
result = gen.generate()
print("=== result ===")
print(result)
print()
decomp = CodeGenerator().generate(result)
print('=== decompiled ===')
print(decomp)
