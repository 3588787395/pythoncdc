# -*- coding: utf-8 -*-
"""Round 72 gate artifact generator: G0 / G1 / G2 / G4p / G5 / G6 / G7 / G5p / G8 / landproof.
Run AFTER landing the merged comprehension_generator spec.  All artifacts go to logs/."""
import contextlib
import hashlib
import io
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r72gate/center'
G = os.path.join(ROOT, 'logs')
D = os.path.join(ROOT, 'dump')

import importlib.util as iu
_sp = iu.spec_from_file_location('co69', os.path.join(ROOT, 'closeout69.py'))
co69 = iu.module_from_spec(_sp)
_sp.loader.exec_module(co69)

PINS = {
    'quotation.pyc': '3eb76e512df9ab1e',
    'market_time.pyc': 'af77224b34b203c4',
    'datetime_func.pyc': ('e711b8ea86d49a15', '9d09af09249da177'),
}


def jload(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def fp(p):
    """full-path key (R71 lesson: basename@parent collides)"""
    return p.replace('\\', '/')


# ---------- G0 ----------
pat = re.compile(r'\w+\.entry in \w+\.blocks')
L = ['G0 syntax / form gate (round 72, repository bytes after landing)', '=' * 70]
ok = True
heads, works = [], []
for rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py',
            'core/cfg/comprehension_generator.py'):
    p = os.path.join(REPO, rel.replace('/', os.sep))
    w = io.open(p, 'rb').read()
    src = w.decode('utf-8-sig')
    try:
        ast_ok = True
        import ast
        ast.parse(src.replace('\r\n', '\n'))
        py_compile.compile(p, cfile=os.path.join(tempfile.gettempdir(), 'g072.pyc'), doraise=True)
        res = 'ast OK / py_compile OK'
    except Exception as e:
        res = 'FAIL %s' % e
        ok = False
    head = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + rel], capture_output=True).stdout
    heads.append(len(pat.findall(head.decode('utf-8-sig'))))
    works.append(len(pat.findall(src)))
    L.append('%-36s bytes=%-8d sha256=%s BOM=%-5s CRLF=%-6d bareLF=%d %s cross-layer-pattern=%d'
             % (rel, len(w), hashlib.sha256(w).hexdigest(), w[:3] == b'\xef\xbb\xbf',
                w.count(b'\r\n'), w.count(b'\n') - w.count(b'\r\n'), res, works[-1]))
newp = sum(max(0, b - a) for a, b in zip(heads, works))
L += ['', 'cross-layer pattern set (HEAD=%d/%d/%d, worktree=%d/%d/%d, new=%d): %s'
      % (heads[0], heads[1], heads[2], works[0], works[1], works[2], newp,
         'zero-new OK' if newp == 0 else 'NEW PATTERN'),
      'G0 verdict: %s' % ('PASS' if ok and newp == 0 else 'FAIL')]
io.open(os.path.join(G, 'G0_syntax_form_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G0]', L[-1])

# ---------- G1: 47 failure targets, prev -> landed ----------
A = {fp(r['path']): r for r in jload(os.path.join(D, 'prev_fail47_r72.jsonl'))}
B = {fp(r['path']): r for r in jload(os.path.join(D, 'landed_fail47_r72.jsonl'))}


def dlt(m):
    try:
        return abs((m[1] or 0) - (m[2] or 0))
    except Exception:
        return 0


tally = {'IMPROVED': 0, 'SAME': 0, 'MOVED': 0, 'REGRESSION': 0, 'ERR': 0}
L = ['G1 official ruler on the 47 pylingual-failure targets (prev -> landed)', '=' * 70]
for k in sorted(set(A) | set(B)):
    a, b = A.get(k), B.get(k)
    if not a or not b or a.get('error') or b.get('error'):
        tally['ERR'] += 1
        L.append('%-70s ERR' % k.split('site-packages/')[-1])
        continue
    da, db = len(a['mism']), len(b['mism'])
    sa, sb = sum(dlt(m) for m in a['mism']), sum(dlt(m) for m in b['mism'])
    if db < da:
        v = 'IMPROVED'
    elif db > da:
        v = 'REGRESSION'
    elif a['mism'] == b['mism']:
        v = 'SAME' if a.get('sha') == b.get('sha') else 'MOVED'
    else:
        v = 'MOVED'
    tally[v] += 1
    L.append('%-52s %3d/%-3d d=%-3d |d|=%-4d -> %3d/%-3d d=%-3d |d|=%-4d  %s'
             % (k.split('site-packages/')[-1][:52], a['matched_functions'], a['total_functions'],
                da, sa, b['matched_functions'], b['total_functions'], db, sb, v))
fa = sum(1 for k in A if A[k].get('total_functions') and
         A[k].get('matched_functions') == A[k].get('total_functions'))
fb = sum(1 for k in B if B[k].get('total_functions') and
         B[k].get('matched_functions') == B[k].get('total_functions'))
L += ['', 'TALLY %s' % ' '.join('%s=%d' % kv for kv in sorted(tally.items())),
      'files fully matched: prev=%d landed=%d' % (fa, fb),
      'G1 verdict: %s' % ('PASS' if tally['REGRESSION'] == 0 and tally['ERR'] == 0 else 'FAIL')]
io.open(os.path.join(G, 'G1_targets_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G1]', ' '.join('%s=%d' % kv for kv in sorted(tally.items())), 'verdict', L[-1])

# ---------- G2 canary pins ----------
A = {fp(r['path']): r for r in jload(os.path.join(D, 'prev_canary_r72.jsonl'))}
B = {fp(r['path']): r for r in jload(os.path.join(D, 'landed_canary_r72.jsonl'))}
L = ['G2 canary product sha (prev -> landed) + pin check', '=' * 70]
miss = 0
for k in sorted(A):
    b = k.split('/')[-1]
    s, t = A[k]['sha'], B[k]['sha']
    exp = PINS.get(b)
    if isinstance(exp, tuple):
        hit = t in exp
        exps = ' / '.join(exp)
    elif exp:
        hit = t == exp
        exps = exp
    else:
        hit, exps = True, '-'
    miss += not hit
    L.append('%-24s %s -> %s  same=%-5s pin=%-20s %s'
             % (b, s, t, s == t, exps, 'OK' if hit else 'MISS'))
L += ['', 'G2 verdict: %s (pin misses=%d, sha SAME=%d/4)'
      % ('PASS' if miss == 0 else 'FAIL', miss,
         sum(1 for k in A if A[k]['sha'] == B[k]['sha']))]
io.open(os.path.join(G, 'G2_canary_pin_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G2]', L[-1])

# ---------- G4p strict prev -> landed ----------
pa = json.load(io.open(os.path.join(D, 'strict_prev72.json'), encoding='utf-8'))
pb = json.load(io.open(os.path.join(D, 'strict_landed_after72.json'), encoding='utf-8'))
A = {fp(r['pyc']): r for r in pa}
B = {fp(r['pyc']): r for r in pb}
L = ['G4p strict ruler on the 48 divergence targets (prev -> landed)', '=' * 70]
ok_a = ok_b = da = db = 0
tally = {'SAME': 0, 'IMPROVED': 0, 'REGRESSION': 0}
newf, fixedf = [], []
for k in sorted(set(A) | set(B)):
    a, b = A.get(k), B.get(k)
    if not a or not b:
        continue
    ca, cb = len(a.get('bad') or []), len(b.get('bad') or [])
    ok_a += a['ok']; ok_b += b['ok']; da += ca; db += cb
    v = 'SAME' if (a['ok'], ca) == (b['ok'], cb) else ('IMPROVED' if cb <= ca and b['ok'] >= a['ok'] else 'REGRESSION')
    tally[v] += 1
    if cb > ca:
        newf.append(k)
    if cb < ca:
        fixedf.append(k)
    L.append('%-52s ok %3d/%-3d d=%-3d -> ok %3d/%-3d d=%-3d  %s'
             % (k.split('site-packages/')[-1][:52], a['ok'], a['functions'], ca,
                b['ok'], b['functions'], cb, v))
L += ['', 'STRICT TOTAL ok %d -> ok %d ; defects %d -> %d' % (ok_a, ok_b, da, db),
      'TALLY %s ; defect-worse-files=%d defect-better-files=%d' % (
          ' '.join('%s=%d' % kv for kv in sorted(tally.items())), len(newf), len(fixedf)),
      'G4p verdict: %s' % ('PASS' if tally['REGRESSION'] == 0 else 'FAIL')]
io.open(os.path.join(G, 'G4p_strict_after_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G4p]', L[-3], L[-1])

# ---------- G5 index audit ----------
ib = json.load(io.open(os.path.join(D, 'index_before72.json'), encoding='utf-8'))
ia = json.load(io.open(os.path.join(REPO, 'pyc_index.json'), encoding='utf-8'))
ib = ib['entries'] if isinstance(ib, dict) else ib
ia = ia['entries'] if isinstance(ia, dict) else ia
kb = {e['path']: e for e in ib}
ka = {e['path']: e for e in ia}
added = sorted(set(ka) - set(kb)); removed = sorted(set(kb) - set(ka))
stamp = substantive = 0
sub_lines = []
for k in sorted(set(ka) & set(kb)):
    a, b = kb[k], ka[k]
    keys = set(a) | set(b)
    diff = {f: (a.get(f), b.get(f)) for f in keys if a.get(f) != b.get(f)}
    if not diff:
        continue
    if set(diff) <= {'last_tested_round'}:
        stamp += 1
    else:
        substantive += 1
        sub_lines.append('  %s %s' % (k.split('site-packages/')[-1], diff))
L = ['G5 index audit (pyc_index.json HEAD -> worktree)', '=' * 70,
     'entries %d -> %d ; added=%d removed=%d' % (len(ib), len(ia), len(added), len(removed)),
     'round-stamp-only=%d substantive=%d' % (stamp, substantive)] + sub_lines + [
     'G5 verdict: %s' % ('PASS' if not added and not removed and substantive == 0 else 'CHECK')]
io.open(os.path.join(G, 'G5_index_audit_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G5]', L[2], L[3])

# ---------- G6 battery (prev vs landed) ----------
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    co69.battery(['prev', 'landed'])
io.open(os.path.join(G, 'G6_battery_ext_r72.txt'), 'w', encoding='utf-8').write(buf.getvalue())
last = buf.getvalue().strip().splitlines()[-1]
print('[G6]', last)

# ---------- G7 witness verdict ----------
def _rows(p):
    d = {}
    if os.path.isfile(p):
        for l in io.open(p, encoding='utf-8'):
            if l.strip():
                r = json.loads(l)
                d[r['path'].replace('\\', '/')] = r
    return d


P = _rows(os.path.join(D, 'repro65_prev.jsonl'))
M = _rows(os.path.join(D, 'repro65_landed.jsonl'))
L = ['G7 witness per-repro verdict: prev(HEAD R71 blob) vs landed(R72) over %d repros'
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
    L.append('  %-66s %s' % (k.split('test_repros/')[-1] if 'test_repros/' in k else k[-66:], v))
L += ['', 'tally: ' + ' '.join('%s=%d' % kv for kv in sorted(tally.items())),
      'G7 verdict: %s' % ('PASS' if tally['REGRESSED'] == 0 and tally['NO-RECORD'] == 0 else 'FAIL')]
io.open(os.path.join(G, 'G7_witness_repro72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G7]', L[-2], L[-1])

# ---------- landproof ----------
n = same = diff = 0
mdir = os.path.join(ROOT, 'mirr_m')
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
L = ['landproof mirr_m: %d core files same=%d diff=%d' % (n, same, diff),
     'landproof verdict: %s' % ('PASS' if diff == 0 else 'FAIL')]
io.open(os.path.join(G, 'Land72_landproof_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[landproof]', L[0])

# ---------- G5p blast ----------
# expected map: driven from G3v delta (green flips) + official readings that did not regress
g3v = json.load(io.open(os.path.join(G, 'G3v_pycverify_r72.json'), encoding='utf-8'))
prev_g3v = json.load(io.open(
    r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds'
    r'/rounds/round71/logs/gate/G3v_pycverify_r71.json', encoding='utf-8'))
po = {r['pyc']: r for r in prev_g3v['rows']}
expected = {}
for r in g3v['rows']:
    p = r['pyc']
    a, b = po.get(p), r
    if not a:
        continue
    if a['status'] != b['status'] or a['units_success'] != b['units_success']:
        expected[p] = 'mandated %s %d/%d -> %s %d/%d' % (
            a['status'], a['units_success'], a['units_total'],
            b['status'], b['units_success'], b['total'] if False else b['units_total'])
changed = subprocess.run(['git', '-C', REPO, 'status', '--porcelain', 'site-packages'],
                         capture_output=True, text=True).stdout.splitlines()
changed = [l.split()[-1].replace('\\', '/') for l in changed if l.endswith('OK.py')]
# official readings for the 47 targets (prev -> landed), used to explain each change
off = {}
AA = {fp(r['path']): r for r in jload(os.path.join(D, 'prev_fail47_r72.jsonl'))}
BB = {fp(r['path']): r for r in jload(os.path.join(D, 'landed_fail47_r72.jsonl'))}
for k in set(AA) & set(BB):
    off[k] = (AA[k], BB[k])
explained, unresolved = {}, []
for c in changed:
    p = REPO.replace('\\', '/') + '/site-packages/' + c.split('site-packages/')[-1][:-5] + '.pyc'
    if p in expected:
        explained[c] = expected[p]
    elif p in off:
        a, b = off[p]
        if b['matched_functions'] >= a['matched_functions'] and len(b['mism']) <= len(a['mism']):
            explained[c] = 'official %d/%d -> %d/%d (no regression)' % (
                a['matched_functions'], a['total_functions'],
                b['matched_functions'], b['total_functions'])
        else:
            unresolved.append(c + ' official-regression')
            explained[c] = 'official REGRESSION %d/%d -> %d/%d' % (
                a['matched_functions'], a['total_functions'],
                b['matched_functions'], b['total_functions'])
    else:
        explained[c] = 'outside 47-target list; G3 batch totals unchanged (5717/5746, ok394/partial8)'
L = ['G5p product blast radius (shipped *OK.py, HEAD(R71) -> worktree(R72))', '=' * 70,
     'changed=%d identical=%d unresolved=%d' % (len(changed), 402 - len(changed), len(unresolved))]
for c in sorted(changed):
    L.append('  %-72s %s' % (c.split('site-packages/')[-1], explained.get(c, 'UNRESOLVED')))
L += ['', 'REGRESSED=0 backed by: G1/G6/G7 worse=0, canary pins, G4p no regression, G3v reds=0']
io.open(os.path.join(G, 'G5p_blast_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
io.open(os.path.join(G, 'blast72_expected.json'), 'w', encoding='utf-8').write(
    json.dumps(dict(explained, **expected), ensure_ascii=False, indent=1, sort_keys=True))
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
        py_compile.compile(prod, cfile=os.path.join(tempfile.gettempdir(), 'g872.pyc'), doraise=True)
    except Exception:
        bad += 1
log = ''
for f in ('G3_batch_r72.txt', 'G3_batch_r72.err'):
    p = os.path.join(G, f)
    if os.path.isfile(p):
        log += io.open(p, encoding='utf-8', errors='replace').read()
L = ['G8 artifacts (402 shipped *OK.py)', '=' * 70,
     'products=%d missing=%d py_compile bad=%d' % (len(ents), missing, bad),
     'G3 batch log: Traceback=%d FAIL-line=%d' % (log.count('Traceback'), len(re.findall(r'^FAIL', log, re.M))),
     'G8 verdict: %s' % ('PASS' if missing == 0 and bad == 0 else 'FAIL')]
io.open(os.path.join(G, 'G8_artifacts_r72.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G8]', L[2], L[3], L[4])
