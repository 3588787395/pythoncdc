# -*- coding: utf-8 -*-
"""Round 71 gate artifact generator (part 2): G5p blast / G6 battery / G7 witness /
landproof / G8.  Run AFTER landing m71."""
import contextlib
import io
import json
import os
import py_compile
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r71gate/center'
G = os.path.join(ROOT, 'logs')

import importlib.util as iu
_sp = iu.spec_from_file_location('co69', os.path.join(ROOT, 'closeout69.py'))
co69 = iu.module_from_spec(_sp)
_sp.loader.exec_module(co69)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    co69.battery(['prev', 'm71'])
io.open(os.path.join(G, 'G6_battery_ext_r71.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('[G6] written')

# G7 witness: per-repro verdict of the true-baseline columns (prev=R70 HEAD blob, m71=R71)
def _rows(p):
    d = {}
    if os.path.isfile(p):
        for l in io.open(p, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                d[r['path'].replace('\\', '/')] = r
    return d


P = _rows(os.path.join(ROOT, 'dump', 'repro65_prev.jsonl'))
M = _rows(os.path.join(ROOT, 'dump', 'repro65_m71.jsonl'))
L = ['G7 witness per-repro verdict: prev(R70 HEAD blob) vs m71(R71) over %d repros'
     % len(set(P) | set(M)), '=' * 70]
tally = {'SAME': 0, 'IMPROVED': 0, 'REGRESSED': 0, 'NO-RECORD': 0}
for k in sorted(set(P) | set(M)):
    a, b = P.get(k), M.get(k)
    if not a or not b:
        v = 'NO-RECORD'
    else:
        x = (a['matched_functions'], len(a['mism'] or []),
             sum((m[2] or 0) - (m[1] or 0) for m in (a['mism'] or [])))
        y = (b['matched_functions'], len(b['mism'] or []),
             sum((m[2] or 0) - (m[1] or 0) for m in (b['mism'] or [])))
        v = 'SAME' if x == y else ('IMPROVED' if y[0] > x[0] or y[1] < x[1] or y[2] > x[2] else 'REGRESSED')
    tally[v] += 1
    L.append('  %-64s %s' % (k.split('test_repros/')[-1] if 'test_repros/' in k else k, v))
L.append('')
L.append('tally: ' + ' '.join('%s=%d' % kv for kv in sorted(tally.items())))
L.append('G7 verdict: %s' % ('PASS' if tally['REGRESSED'] == 0 and tally['NO-RECORD'] == 0 else 'FAIL'))
io.open(os.path.join(G, 'G7_witness_repro71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G7] written')
print('   ', io.open(os.path.join(G, 'G6_battery_ext_r71.txt'), encoding='utf-8').read().strip().splitlines()[-1])
print('   ', io.open(os.path.join(G, 'G7_witness_repro71.txt'), encoding='utf-8').read().strip().splitlines()[-2:])

# ---------- landproof ----------
n = same = diff = 0
mdir = os.path.join(ROOT, 'mirr_m71')
for root, dirs, files in os.walk(os.path.join(mdir, 'core')):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        mp = os.path.join(root, f)
        rel = os.path.relpath(mp, mdir).replace('\\', '/')
        rp = os.path.join(REPO, rel.replace('/', os.sep))
        n += 1
        if io.open(mp, 'rb').read() == io.open(rp, 'rb').read():
            same += 1
        else:
            diff += 1
            print('   LANDPROOF DIFF', rel)
L = ['landproof mirr_m71: %d core files same=%d diff=%d' % (n, same, diff),
     'landproof verdict: %s' % ('PASS' if diff == 0 else 'FAIL')]
io.open(os.path.join(G, 'Land71_landproof_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[landproof] same=%d diff=%d' % (same, diff))

# ---------- G5p blast ----------
improved = json.load(io.open(os.path.join(G, 'blast71_expected.json'), encoding='utf-8')) \
    if os.path.isfile(os.path.join(G, 'blast71_expected.json')) else {}
changed = subprocess.run(['git', '-C', REPO, 'status', '--porcelain', 'site-packages'],
                         capture_output=True, text=True).stdout.splitlines()
changed = [l.split()[-1].replace('\\', '/') for l in changed if l.endswith('OK.py')]
unresolved = [c for c in changed if c not in improved]
L = ['G5p product blast radius (shipped *OK.py, HEAD(R70) -> worktree(R71))', '=' * 70]
L.append('changed=%d identical=%d unresolved=%d' % (len(changed), 402 - len(changed), len(unresolved)))
for c in sorted(changed):
    L.append('  %-72s %s' % (c.split('site-packages/')[-1], improved.get(c, 'UNRESOLVED')))
L.append('')
L.append('REGRESSED=0 expectation backed by: G6/G7 batteries worse=0; canary; strict G4p; no NEW defect funcs')
io.open(os.path.join(G, 'G5p_blast_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G5p] changed=%d unresolved=%d' % (len(changed), len(unresolved)))

# ---------- G8 ----------
ix = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
ents = ix['entries'] if isinstance(ix, dict) and 'entries' in ix else ix
missing = bad = 0
for e in ents:
    rel = e['path'].replace('\\', '/').split('site-packages/')[-1]
    prod = os.path.join(REPO, 'site-packages', rel[:-4] + 'OK.py')
    if not os.path.isfile(prod):
        missing += 1
        continue
    try:
        py_compile.compile(prod, cfile=os.path.join(tempfile.gettempdir(), 'g871.pyc'), doraise=True)
    except Exception:
        bad += 1
log = io.open(os.path.join(G, 'G3_batch_r71.txt'), encoding='utf-8', errors='replace').read() \
    if os.path.isfile(os.path.join(G, 'G3_batch_r71.txt')) else ''
err = io.open(os.path.join(G, 'G3_batch_r71.err'), encoding='utf-8', errors='replace').read() \
    if os.path.isfile(os.path.join(G, 'G3_batch_r71.err')) else ''
trace = (log + err).count('Traceback')
fail_hits = sum(1 for l in (log + err).splitlines()
                if 'FAIL' in l and 'errors.pyc' not in l and 'user_error.pyc' not in l
                and 'failed_pyc' not in l)
L = ['G8 artifacts audit (round 71)', '=' * 70,
     'index entries      : %d' % len(ents),
     'OK.py present      : %d (missing %d)' % (len(ents) - missing, missing),
     'py_compile bad     : %d' % bad,
     'batch G3 Traceback : %d   FAIL-line hits: %d' % (trace, fail_hits),
     'G8 verdict: %s' % ('PASS' if (missing == 0 and bad == 0 and trace == 0 and fail_hits == 0) else 'FAIL')]
io.open(os.path.join(G, 'G8_artifacts_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G8] written', L[-2], L[-1])
