import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, MatchRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

src = 'match a:\n    case {"key": 1}:\n        pass'
code = compile(src, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
code_gen = CodeGenerator()
output = code_gen.generate(result)
print('OUTPUT:')
print(output)
