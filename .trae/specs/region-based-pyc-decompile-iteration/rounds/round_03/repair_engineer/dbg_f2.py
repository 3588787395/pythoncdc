import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import decompile
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, Region
from core.cfg.region_ast_generator import RegionASTGenerator

src = '''class C:
    X = X

    def m(self):
        return 1
'''
code = compile(src, '<f2>', 'exec')
# class code object
cls = [c for c in code.co_consts if isinstance(c, types.CodeType) and c.co_name=='C'][0]
cfg = CFGBuilder().build(cls)
an = RegionAnalyzer(cfg)
regions = an.analyze()
print("=== regions ===")
for r in regions:
    name = getattr(r,'region_type', type(r).__name__)
    blk = ','.join(str(b.start_offset) for b in sorted(getattr(r,'blocks',set()), key=lambda x:x.start_offset))
    print(f"[{name}] blocks={{{blk}}}")

print("=== generate ===")
print(decompile(src,'<f2>'))
