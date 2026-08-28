#!/usr/bin/env python
"""Round 03 探针：追踪 _process_if_blocks 与 _generate_region 调用时序。"""
import sys
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
import core.cfg.region_ast_generator as rag
from core.cfg.region_ast_generator import RegionASTGenerator

SRC = "def f(engine):\n    if engine.a:\n        if engine.b:\n            engine.c()\n        engine.a = engine.a or 10\n"

_orig_pib = RegionASTGenerator._process_if_blocks
def pib(self, blocks, region, branch='then'):
    offs = sorted(b.start_offset for b in blocks)
    print(f'PIB  region@{getattr(getattr(region,"entry",None),"start_offset",None)} branch={branch} blocks={offs}')
    r = _orig_pib(self, blocks, region, branch)
    kinds = [(s.get('type'), s.get('targets') is not None) for s in r] if isinstance(r, list) else r
    print(f'PIB-> {kinds}')
    return r
RegionASTGenerator._process_if_blocks = pib

_orig_gen = RegionASTGenerator._generate_region
def gen(self, region, *a, **kw):
    rt = getattr(getattr(region, 'region_type', None), 'name', '?')
    entry = getattr(getattr(region, 'entry', None), 'start_offset', None)
    print(f'GEN  {rt}@{entry}')
    return _orig_gen(self, region, *a, **kw)
RegionASTGenerator._generate_region = gen

# also trace boolop generation
if hasattr(RegionASTGenerator, '_generate_boolop'):
    _orig_bo = RegionASTGenerator._generate_boolop
    def bo(self, region, *a, **kw):
        entry = getattr(getattr(region, 'entry', None), 'start_offset', None)
        print(f'BOOLOP_GEN @{entry}')
        return _orig_bo(self, region, *a, **kw)
    RegionASTGenerator._generate_boolop = bo

code_obj = compile(SRC, '<p9>', 'exec')
fn = [c for c in code_obj.co_consts if isinstance(c, type(code_obj))][0]
cfg = build_cfg(fn)
g = RegionASTGenerator(cfg)
g.generate()
