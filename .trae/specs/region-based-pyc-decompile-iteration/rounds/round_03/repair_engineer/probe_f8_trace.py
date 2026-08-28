#!/usr/bin/env python
"""Round 03 探针：插桩 _generate_region 观察区域生成顺序。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionType

SRC = "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = engine.a or 10\n"

_orig = RegionASTGenerator._generate_region

def traced(self, region, *a, **kw):
    rt = getattr(getattr(region, 'region_type', None), 'name', '?')
    entry = getattr(getattr(region, 'entry_block', None) or getattr(region, 'entry', None), 'start_offset', None)
    blocks = sorted(getattr(b, 'start_offset', -1) for b in (getattr(region, 'blocks', None) or []))
    print(f'GEN  type={rt:12s} entry={entry} blocks={blocks}')
    r = _orig(self, region, *a, **kw)
    print(f'DONE type={rt:12s} entry={entry} -> {type(r).__name__}')
    return r

RegionASTGenerator._generate_region = traced

code_obj = compile(SRC, '<p9>', 'exec')
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()
import json
print(json.dumps(ast_dict, ensure_ascii=False, default=str)[:2000])
