#!/usr/bin/env python
"""Round 03 探针：打印 boolop 生成调用栈。"""
import sys, traceback
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = engine.a or 10\n"

_orig_bo = RegionASTGenerator._generate_boolop
def bo(self, region, *a, **kw):
    entry = getattr(getattr(region, 'entry', None), 'start_offset', None)
    print(f'=== BOOLOP_GEN @{entry} CALL STACK ===')
    st = traceback.extract_stack()[:-1]
    for fr in st[-14:]:
        print(f'  {fr.filename.split(chr(92))[-1]}:{fr.lineno} {fr.name}  |  {fr.line[:80] if fr.line else ""}')
    return _orig_bo(self, region, *a, **kw)
RegionASTGenerator._generate_boolop = bo

code_obj = compile(SRC, '<p9>', 'exec')
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)
g = RegionASTGenerator(cfg)
g.generate()
