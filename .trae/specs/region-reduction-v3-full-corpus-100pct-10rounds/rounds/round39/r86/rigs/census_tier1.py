"""Tier-1 corpus census (analyzer-only, cheap): every TernaryRegion arm for which the [R21-55c]
exception-successor relaxation is the ONLY thing that lets `_adopt_arm` pass, i.e. the arm has a
non-merge successor whose first instruction is PUSH_EXC_INFO / WITH_EXCEPT_START.

Counting rule:
  REGION   = TernaryRegion present after RegionAnalyzer.analyze (per code object)
  ELIGIBLE = an arm of that region has >=1 non-merge successor AND every such successor is an
             exception-entry block, with >=1 of them (i.e. the arm is not merge-only)  [C's own
             relaxation condition]
  REFUSED  = ELIGIBLE and the [R21-56] conjunct declines it (evaluated by the same predicate
             the candidate installs, run read-only here)

usage: python -X utf8 work/census_tier1.py <out.json> <shard-idx> <shard-count>
"""
import json
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
SP = os.path.join(REPO, "site-packages")
OUT = sys.argv[1]
SHARD = int(sys.argv[2])
NSHARDS = int(sys.argv[3])

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TernaryRegion

EXC_ENTRY = ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')

allpyc = []
for root, dirs, files in os.walk(SP):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.pyc'):
            allpyc.append(os.path.join(root, f))
allpyc.sort()
mine = [p for i, p in enumerate(allpyc) if i % NSHARDS == SHARD]


def walk(c):
    yield c
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)


def arm_classify(arm, merge):
    """Return (relaxation_needed, non_merge_offsets, first_opnames)."""
    if arm is None:
        return None
    succs = [s for s in (getattr(arm, 'successors', None) or set()) if s is not None]
    non_merge = [s for s in succs if s is not merge]
    if not non_merge:
        return None
    firsts = []
    for s in non_merge:
        fi = s.get_first_instruction() if getattr(s, 'instructions', None) else None
        firsts.append(fi.opname if fi is not None else '')
    relaxed = all(f in EXC_ENTRY for f in firsts)
    return (relaxed, [s.start_offset for s in non_merge], firsts)


files = {}
for p in mine:
    rel = os.path.relpath(p, SP).replace(os.sep, '/')
    st = {'regions': 0, 'eligible': 0, 'sites': [], 'err': None}
    try:
        mod = load_pyc_file_v2(p)
        code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
        if hasattr(code, 'to_python_code'):
            code = code.to_python_code()
        for co in walk(code):
            try:
                cfg = build_cfg(co)
                an = RegionAnalyzer(cfg)
                an.analyze()
                regions = list(getattr(an, 'regions', []) or [])
            except Exception:
                continue
            for r in regions:
                if not isinstance(r, TernaryRegion):
                    continue
                st['regions'] += 1
                merge = getattr(r, 'merge_block', None)
                for a in (getattr(r, 'true_value_block', None),
                          getattr(r, 'false_value_block', None)):
                    cls = arm_classify(a, merge)
                    if cls is None or not cls[0]:
                        continue
                    st['eligible'] += 1
                    st['sites'].append({
                        'co': getattr(co, 'co_qualname', co.co_name),
                        'cond': getattr(r.condition_block, 'start_offset', None),
                        'arm': a.start_offset,
                        'merge': getattr(merge, 'start_offset', None),
                        'non_merge_succs': cls[1],
                    })
    except Exception as e:
        st['err'] = repr(e)[:120]
    files[rel] = st

tot = {'regions': sum(v['regions'] for v in files.values()),
       'eligible': sum(v['eligible'] for v in files.values())}
print('SHARD %d/%d files=%d regions=%d eligible_arm_sites=%d' %
      (SHARD, NSHARDS, len(files), tot['regions'], tot['eligible']))
for rel, v in files.items():
    if v['eligible'] or v['err']:
        print('  %-62s eligible=%d %s' % (rel, v['eligible'], (v['sites'][:3] if v['eligible'] else v['err'])))
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
json.dump({'shard': [SHARD, NSHARDS], 'totals': tot, 'files': files},
          open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
