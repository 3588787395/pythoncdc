# -*- coding: utf-8 -*-
"""Dump basic blocks and regions for one code object.

usage: python -X utf8 w50struct.py <pyc> <func-name>
"""
import importlib.util
import sys
import types as _t

REPO = r'F:\Downloads\pythoncdc-main'
PYC, NAME = sys.argv[1], sys.argv[2]
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('pc50s', REPO + '/pycdc.py')
pc = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pc)
mod = pc.load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer


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
    blks = it(cfg.blocks)
    print('==== BLOCKS (%d) ====' % len(blks))
    for b in sorted(blks, key=lambda x: (off(x) is None, off(x))):
        last = b.get_last_instruction()
        n = len(list(b.instructions))
        print('B@%-6s ninstr=%-4s ter=%-30s nsucc=%d succs=%s npred=%d preds=%s' % (
            off(b), n, last.opname if last else '?', len(it(b.successors)),
            sorted(off(x) for x in it(b.successors)),
            len(it(b.predecessors)), sorted(off(x) for x in it(b.predecessors))))
    ra = RegionAnalyzer(cfg)
    ra.analyze()
    print('==== REGIONS (%d) ====' % len(ra.regions))
    for r in sorted(it(ra.regions), key=lambda x: (off(getattr(x, 'entry', None)) is None,
                                                   off(getattr(x, 'entry', None)))):
        blk = sorted(off(b) for b in it(getattr(r, 'blocks', None)))
        print('%-22s entry=%-6s then=%s else=%s merge=%-6s cond=%-6s blocks=%s' % (
            type(r).__name__, off(getattr(r, 'entry', None)),
            [off(x) for x in it(getattr(r, 'then_blocks', None))],
            [off(x) for x in it(getattr(r, 'else_blocks', None))],
            off(getattr(r, 'merge_block', None)),
            off(getattr(r, 'condition_block', None) or getattr(r, 'header_block', None)),
            blk))
    break
