# -*- coding: utf-8 -*-
"""Run the analyzer from a (possibly instrumented) mirror core on one function.

usage: python -X utf8 run50.py <mirror-dir> <pyc> <func-name>
"""
import importlib.util
import os
import sys
import types as _t

MIRROR = sys.argv[1]
PYC, NAME = sys.argv[2], sys.argv[3]
REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
for k in [k for k in sys.modules if k == 'core' or k.startswith('core.')]:
    del sys.modules[k]
_s = importlib.util.spec_from_file_location('pc50r', os.path.join(MIRROR, 'pycdc.py'))
pc = importlib.util.module_from_spec(_s)
sys.path.insert(1, MIRROR)
_s.loader.exec_module(pc)
mod = pc.load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
import core.cfg.region_analyzer as _ramod
import traceback as _tb

TRACE = int(os.environ.get('R50TRACE', '0'))
if TRACE:
    for _cn in ('IfRegion', 'TernaryRegion', 'Region'):
        _orig = getattr(_ramod, _cn, None)
        if _orig is None:
            continue

        def _mk(orig=_orig, cn=_cn):
            class _Traced(orig):
                def __init__(self, *a, **kw):
                    super().__init__(*a, **kw)
                    try:
                        e = getattr(self, 'entry', None)
                        eo = getattr(e, 'start_offset', None)
                    except Exception:
                        eo = None
                    if eo == TRACE:
                        fr = [x for x in _tb.extract_stack()
                              if 'region_analyzer' in x.filename][-4:]
                        print('BUILD %s entry=%s merge=%s then=%s else=%s' % (
                            cn, eo,
                            off(getattr(self, 'merge_block', None)),
                            [off(x) for x in (getattr(self, 'then_blocks', None) or [])],
                            [off(x) for x in (getattr(self, 'else_blocks', None) or [])]))
                        for f in fr:
                            print('   at %s:%d %s' % (
                                f.filename.split('\\\\')[-1], f.lineno,
                                (f.line or '').strip()[:70]))
            return _Traced
        setattr(_ramod, _cn, _mk())
assert RegionAnalyzer.__module__.startswith('core.'), RegionAnalyzer.__module__
print('core from:', os.path.dirname(sys.modules['core'].__file__))


def off(b):
    return getattr(b, 'start_offset', None) if b is not None else None


def it(x):
    if x is None:
        return []
    if isinstance(x, dict):
        return list(x.values())
    return list(x)


def walk2(co, path=''):
    yield path, co
    for c in co.co_consts:
        if isinstance(c, _t.CodeType):
            yield from walk2(c, path + '/' + c.co_name)


for p, co in walk2(code):
    if co.co_name != NAME:
        continue
    cfg = build_cfg(co)
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    print('==== REGIONS (%d) ====' % len(it(ra.regions)))
    for r in sorted(it(ra.regions), key=lambda x: (off(getattr(x, 'entry', None)) is None,
                                                   off(getattr(x, 'entry', None)))):
        print('%-22s entry=%-6s then=%s else=%s merge=%-6s blocks=%s' % (
            type(r).__name__, off(getattr(r, 'entry', None)),
            [off(x) for x in it(getattr(r, 'then_blocks', None))],
            [off(x) for x in it(getattr(r, 'else_blocks', None))],
            off(getattr(r, 'merge_block', None)),
            sorted(off(b) for b in it(getattr(r, 'blocks', None)))))
    break
