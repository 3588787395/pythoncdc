"""Run the full region pipeline on one pyc with the PROBE-patched generator installed and dump
every `_adopt_arm` adoption + the `_ternary_host_call_prefix_span` verdicts.

usage: python -X utf8 work/probe_run.py <abs pyc> [--quiet]
"""
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
sys.path.insert(0, os.path.join(MIRROR, 'core'))

PYC = sys.argv[1]

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_ast_generator as g
from core.cfg.region_ast_generator import RegionASTGenerator

mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()

RESULTS = []
_orig = RegionASTGenerator._ternary_host_call_prefix_span


def _wrapped(self, region):
    del g._R2156_PROBE[:]
    res = _orig(self, region)
    ev = [dict(e) for e in g._R2156_PROBE]
    RESULTS.append({
        'cond': getattr(region.condition_block, 'start_offset', None),
        'relaxed_adoptions': [e for e in ev if e['relaxed']],
        'adoptions': ev,
        'result': None if res is None else {
            'lo': res[0][0].offset, 'hi': res[0][-1].offset,
            'last_op': res[0][-1].opname, 'n_instrs': len(res[0]),
            'blocks': sorted(b.start_offset for b in res[1]),
            'prefix_n': len(res[2]), 'tail_n': len(res[3]),
        },
    })
    return res


RegionASTGenerator._ternary_host_call_prefix_span = _wrapped

_HPT = RegionASTGenerator._generate_host_prefix_ternary_statement
STATS = []


def _wrapped2(self, region, span_instrs, span_blocks, prefix_instrs, tail_instrs):
    st = _HPT(self, region, span_instrs, span_blocks, prefix_instrs, tail_instrs)
    STATS.append({
        'cond': getattr(region.condition_block, 'start_offset', None),
        'close': span_instrs[-1].offset if span_instrs else None,
        'types': None if st is None else [s.get('type') for s in st],
        'tail_first': [(i.opname, i.offset) for i in tail_instrs[:3]],
        'tail_last': [(i.opname, i.offset) for i in tail_instrs[-3:]],
        'tail_n': len(tail_instrs),
    })
    return st


RegionASTGenerator._generate_host_prefix_ternary_statement = _wrapped2


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


quiet = '--quiet' in sys.argv
for co in walk(code):
    del g._R2156_PROBE[:]
    del STATS[:]
    RESULTS.append(None)
    try:
        cfg = build_cfg(co)
        gen = RegionASTGenerator(cfg, top_level_code=co if co.co_name == '<module>' else None)
        gen.generate()
    except Exception as exc:
        print('ERR', co.co_name, repr(exc)[:100])
    rows = [r for r in RESULTS if r]
    RESULTS[:] = []
    fired = [r for r in rows if r['result'] is not None or r['relaxed_adoptions']]
    if not fired:
        continue
    print('==== co_name=%s qual=%s  calls=%d' % (co.co_name, getattr(co, 'co_qualname', co.co_name), len(rows)))
    for r in fired:
        print('  cond@%-7s relaxed_adoptions=%s  result=%s' % (
            r['cond'], [(e['arm'], e['merge'], e['ops'][:3]) for e in r['relaxed_adoptions']],
            r['result']))
        if not quiet:
            for e in r['adoptions']:
                print('      arm@%-6s merge@%-6s relaxed=%s succs=%s succ_first=%s ops=%s'
                      % (e['arm'], e['merge'], e['relaxed'], e['succs'], e['succ_first'], e['ops'][:6]))
    for s in STATS:
        print('  EMIT cond@%-7s close@%-7s types=%s tail_n=%s tail_first=%s tail_last=%s'
              % (s['cond'], s['close'], s['types'], s['tail_n'], s['tail_first'], s['tail_last']))
