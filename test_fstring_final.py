import sys
sys.path.insert(0, '.')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

src = "def f(direction):\n    return f\"{'IN' if direction == '0' else 'OUT'}END\""

code = compile(src, '<test>', 'exec')
for c in code.co_consts:
    if hasattr(c, 'co_code'):
        cfg = build_cfg(c)
        ra = RegionAnalyzer(cfg)
        ra.analyze()
        gen = RegionASTGenerator(cfg, ra)
        ast_obj = gen.generate()
        import json
        print(json.dumps(ast_obj, indent=2, default=str))
