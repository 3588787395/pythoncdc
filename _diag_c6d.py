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

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"Regions type: {type(regions)}")
print(f"Regions count: {len(regions)}")
for r in regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")
