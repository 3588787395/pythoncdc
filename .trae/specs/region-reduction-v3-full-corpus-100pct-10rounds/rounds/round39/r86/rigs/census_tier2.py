"""Tier-2 census (full pipeline, PROBE generator installed): for every span produced by
`_ternary_host_call_prefix_span`, record whether the [R21-55c] exception-successor relaxation was
used, and evaluate the [R21-56] tail-boundary conjunct read-only.

Counting rule:
  CALLS   = `_ternary_host_call_prefix_span` invocations (each TernaryRegion is examined)
  FIRED   = returned a span (the host-call fold takes over)
  RELAXED = >=1 arm adopted only because its non-merge successors were exception entries
  PERMIT  = RELAXED and FIRED and the closing block's tail (if any) ends on a statement boundary
  REFUSE  = RELAXED and FIRED and the tail ends on a conditional jump / value producer

usage: python -X utf8 work/census_tier2.py <pathlist-file> [out.json]
"""
import json
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")

LIST = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else None

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_ast_generator as g
from core.cfg.region_ast_generator import RegionASTGenerator

_BOUNDARY_PREFIX = ('STORE_', 'JUMP_')
_BOUNDARY_OPS = ('POP_TOP', 'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS')


def is_boundary(opname):
    if opname.startswith('POP_JUMP') or opname.startswith('JUMP_IF'):
        return False
    return opname in _BOUNDARY_OPS or opname.startswith(_BOUNDARY_PREFIX)


ROWS = []
_relaxed_here = []

_SPAN = RegionASTGenerator._ternary_host_call_prefix_span
_HPT = RegionASTGenerator._generate_host_prefix_ternary_statement


def _span_wrapped(self, region):
    del g._R2156_PROBE[:]
    del _relaxed_here[:]
    res = _SPAN(self, region)
    relaxed = any(e['relaxed'] for e in g._R2156_PROBE)
    ROWS.append({
        'cond': getattr(region.condition_block, 'start_offset', None),
        'fired': res is not None,
        'relaxed': relaxed,
        'close': res[0][-1].offset if res else None,
        'tail_n': len(res[3]) if res else 0,
        'tail_last': res[3][-1].opname if res and res[3] else None,
    })
    return res


def _hpt_wrapped(self, region, span_instrs, span_blocks, prefix_instrs, tail_instrs):
    _relaxed_here.append(1)
    return _HPT(self, region, span_instrs, span_blocks, prefix_instrs, tail_instrs)


RegionASTGenerator._ternary_host_call_prefix_span = _span_wrapped
RegionASTGenerator._generate_host_prefix_ternary_statement = _hpt_wrapped


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


rels = [l.strip() for l in open(LIST, encoding='utf-8') if l.strip()]
summary = {}
for rel in rels:
    p = os.path.join(REPO, rel.replace('/', os.sep))
    ROWS[:] = []
    try:
        mod = load_pyc_file_v2(p)
        code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
        if hasattr(code, 'to_python_code'):
            code = code.to_python_code()
        for co in walk(code):
            try:
                cfg = build_cfg(co)
                gen = RegionASTGenerator(cfg, top_level_code=co if co.co_name == '<module>' else None)
                gen.generate()
            except Exception:
                continue
    except Exception as e:
        summary[rel] = {'err': repr(e)[:100]}
        continue
    rows = ROWS[:]
    fired = [r for r in rows if r['fired']]
    relaxed = [r for r in rows if r['fired'] and r['relaxed']]
    refuse = [r for r in relaxed if r['tail_last'] is not None and not is_boundary(r['tail_last'])]
    permit = [r for r in relaxed if r not in refuse]
    summary[rel] = {'calls': len(rows), 'fired': len(fired), 'relaxed_fired': len(relaxed),
                    'permit': len(permit), 'refuse': len(refuse),
                    'refuse_sites': [r for r in refuse],
                    'permit_tails': sorted({(r['cond'], r['tail_last']) for r in permit})}
    s = summary[rel]
    print('%-60s calls=%-4d fired=%-3d relaxed=%-3d PERMIT=%-3d REFUSE=%-3d %s' %
          (rel, s['calls'], s['fired'], s['relaxed_fired'], s['permit'], s['refuse'],
           [(r['cond'], r['tail_last']) for r in refuse] or ''))
tot = {k: sum(v.get(k, 0) for v in summary.values()) for k in ('calls', 'fired', 'relaxed_fired', 'permit', 'refuse')}
print('TOTAL files=%d %s' % (len(rels), tot))
if OUT:
    json.dump(summary, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
