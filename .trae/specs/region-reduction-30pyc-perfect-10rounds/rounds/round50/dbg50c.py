# -*- coding: utf-8 -*-
"""Copy an arm mirror and add chain-merge diagnostics incl. R50-B internals.

usage: python -X utf8 dbg50c.py <src-mirror-dir> <dst-mirror-dir> [header-offset]
"""
import io
import os
import shutil
import sys

SRC, DST = sys.argv[1], sys.argv[2]
HDR = int(sys.argv[3]) if len(sys.argv) > 3 else 130
sys.stdout.reconfigure(encoding='utf-8')
if os.path.exists(DST):
    shutil.rmtree(DST)
os.makedirs(os.path.dirname(DST), exist_ok=True)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

P = DST + '/core/cfg/region_analyzer.py'
u = io.open(P, encoding='utf-8-sig', newline='').read()
nl = '\r\n' if u.count('\r') else '\n'
t = u.replace('\r\n', '\n').replace('\r', '\n')
L = t.split('\n')

ANCHOR = '            if _chain_merge_candidates:'
idx = [i for i, l in enumerate(L) if l == ANCHOR]
assert len(idx) == 1, idx
i = idx[0]
dbg = [
    '            if getattr(block, "start_offset", None) == %d:' % HDR,
    '                def _o(b):',
    '                    return getattr(b, "start_offset", None)',
    '                print("R50CHAIN H=", _o(block),',
    '                      " conds=", [_o(x) for x in elif_info.get("conditions", [])],',
    '                      " bodies=", [[_o(x) for x in _cb] for _cb in elif_info.get("bodies", [])],',
    '                      " fe=", [_o(x) for x in elif_info.get("final_else", [])],',
    '                      " exits=", [sorted(_o(x) for x in _s) for _s in _all_branch_exits],',
    '                      " nonempty=", len(_non_empty_exits),',
    '                      " cands=", sorted(_o(x) for x in _chain_merge_candidates),',
    '                      " struct=", sorted(_o(x) for x in _r50b_struct),',
    '                      " tris=", [(_o(_t0.entry), sorted(_o(_t1) for _t1 in (_t0.blocks or [])))',
    '                                  for _t0 in (ternary_regions or [])',
    '                                  if isinstance(_t0, TernaryRegion)],',
    '                      " owned=", sorted(_o(x) for x in _r50b_owned))',
]
# _r50b_* names only exist in arms that carry the R50-B edit; guard per-name.
has_b = any('_r50b_struct =' in l for l in L)
if not has_b:
    dbg = [l for l in dbg
           if 'struct=' not in l and 'owned=' not in l]
    print('(note: src has no R50-B names; structural prints only)')
L[i:i] = dbg
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(L).replace('\n', nl))
print('diagnostics inserted at line %d of %s' % (i + 1, P))
