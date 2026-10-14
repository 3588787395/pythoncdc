"""Measure whether the landed [R21-55]/[R21-56] rules have any action surface on
TradeLiveBroker._sync_worker (and corpus-wide census on the broker pyc).

usage: python -X utf8 work/r2155_reach.py <abs pyc>
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_analyzer as ra
import core.cfg.region_ast_generator as g
from core.cfg.region_ast_generator import RegionASTGenerator

PYC = sys.argv[1]
mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()

LOG = []
_ORIG = ra.RegionAnalyzer._r2155_diamond_join_from_value_blocks


def _w(self, true_block, false_block):
    co = getattr(self.cfg, 'code', None)
    tb = true_block.start_offset if true_block is not None else None
    fb = false_block.start_offset if false_block is not None else None
    try:
        res = _ORIG(self, true_block, false_block)
    except Exception as e:
        LOG.append(('ERR', getattr(co, 'co_name', '?'), tb, fb, repr(e)))
        raise
    LOG.append(('JOIN', getattr(co, 'co_name', '?'), tb, fb,
                res.start_offset if res is not None else None))
    return res


ra.RegionAnalyzer._r2155_diamond_join_from_value_blocks = _w

_ORIG56 = RegionASTGenerator._r2156_tail_is_bounded_statements


def _w56(self, tail):
    r = _ORIG56(self, tail)
    LOG.append(('R2156', None, tail[0].offset if tail else None,
                tail[-1].opname if tail else None, r))
    return r


RegionASTGenerator._r2156_tail_is_bounded_statements = _w56

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
gen.generate()

from collections import Counter
c = Counter(x[0] for x in LOG)
print('counters', dict(c))
join = [x for x in LOG if x[0] == 'JOIN']
print('JOIN calls=%d FIRES=%d' % (len(join), len([x for x in join if x[4] is not None])))
for x in join:
    print('  join co=%s true=%s false=%s -> %s' % (x[1], x[2], x[3], x[4]))
r56 = [x for x in LOG if x[0] == 'R2156']
print('R2156 calls=%d TRUE=%d FALSE=%d' % (len(r56), len([x for x in r56 if x[4]]),
                                           len([x for x in r56 if x[4] is False])))
# which code objects did JOIN calls come from?
print('JOIN cos', sorted(set(x[1] for x in join)))
