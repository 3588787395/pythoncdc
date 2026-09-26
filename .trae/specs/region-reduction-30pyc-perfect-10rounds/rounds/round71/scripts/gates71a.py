# -*- coding: utf-8 -*-
"""Round 71 gate artifact generator (part 1): G0 / G1(56 targets) / G2 canary / G4p strict.
Run AFTER landing m71.  Baselines: dump/landed56_r71.jsonl, dump/landed_canary_r71.jsonl,
strict_landed_r71.json (written pre-landing or on landed build)."""
import ast
import hashlib
import io
import json
import os
import py_compile
import re
import subprocess
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/opencode/r71gate/center'
G = os.path.join(ROOT, 'logs')
D = os.path.join(ROOT, 'dump')


def jload(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def base(p):
    q = p.replace('\\', '/')
    return q.split('/')[-1] + '@' + (q.split('/')[-2] if '/' in q else '')


# ---------- G0 ----------
pat = re.compile(r'region\.entry\s+in\s+\w+\.blocks')
L = ['G0 syntax / form gate (round 71, repository bytes after landing)', '=' * 70]
ok = True
landed_counts = []
rels = ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py',
        'core/cfg/comprehension_generator.py')
work_counts = []
for rel in rels:
    p = os.path.join(REPO, rel.replace('/', os.sep))
    w = io.open(p, 'rb').read()
    src = w.decode('utf-8-sig')
    try:
        ast.parse(src.replace('\r\n', '\n'))
        py_compile.compile(p, cfile=os.path.join(tempfile.gettempdir(), 'g0a71.pyc'), doraise=True)
        res = 'ast OK / py_compile OK'
    except Exception as e:
        res = 'FAIL %s' % e
        ok = False
    head = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + rel], capture_output=True).stdout
    landed_counts.append(len(pat.findall(head.decode('utf-8-sig'))))
    work_counts.append(len(pat.findall(src)))
    L.append('%-36s bytes=%-8d sha256=%s BOM=%-5s CRLF=%-6d bareLF=%d %s cross-layer-pattern=%d'
             % (rel, len(w), hashlib.sha256(w).hexdigest(), w[:3] == b'\xef\xbb\xbf',
                w.count(b'\r\n'), w.count(b'\n') - w.count(b'\r\n'), res, work_counts[-1]))
newpats = sum(max(0, b - a) for a, b in zip(landed_counts, work_counts))
L.append('')
L.append('cross-layer pattern set (landed=%d/%d/%d, merged=%d/%d/%d, new=%d): %s'
         % (landed_counts[0], landed_counts[1], landed_counts[2],
            work_counts[0], work_counts[1], work_counts[2], newpats,
            'zero-new OK' if newpats == 0 else 'NEW PATTERN'))
L.append('G0 verdict: %s' % ('PASS' if ok else 'FAIL'))
io.open(os.path.join(G, 'G0_syntax_form_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G0] written')

# ---------- G1: 56-target official tally (landed -> m71) ----------
A = {base(r['path']): r for r in jload(os.path.join(D, 'landed56_r71.jsonl'))}
B = {base(r['path']): r for r in jload(os.path.join(D, 'm71_56.jsonl'))}


def delta(m):
    try:
        return abs((m[1] or 0) - (m[2] or 0))
    except Exception:
        return 0


tally = {'IMPROVED': 0, 'SAME': 0, 'MOVED': 0, 'REGRESSION': 0, 'ERR': 0}
L = ['G1 official ruler on the 56 pylingual-failure targets (landed -> m71)', '=' * 70]
for k in sorted(A):
    a, b = A[k], B[k]
    if a.get('error') or b.get('error'):
        tally['ERR'] += 1
        L.append('%-46s ERR' % k.split('@')[0])
        continue
    da, db = len(a['mism']), len(b['mism'])
    sa, sb = sum(delta(m) for m in a['mism']), sum(delta(m) for m in b['mism'])
    if db < da:
        v = 'IMPROVED'
    elif db > da:
        v = 'REGRESSION'
    elif a['mism'] == b['mism']:
        v = 'SAME' if a.get('sha') == b.get('sha') else 'MOVED'
    else:
        v = 'MOVED'
    tally[v] += 1
    L.append('%-46s %3d/%-3d d=%-3d |d|=%-4d -> %3d/%-3d d=%-3d |d|=%-4d  %s'
             % (k.split('@')[0], a['matched_functions'], a['total_functions'], da, sa,
                b['matched_functions'], b['total_functions'], db, sb, v))
L.append('')
L.append('TALLY %s' % ' '.join('%s=%d' % kv for kv in sorted(tally.items())))
io.open(os.path.join(G, 'G1_targets_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G1] written', tally)

# ---------- G2 canary ----------
A = {base(r['path']): r for r in jload(os.path.join(D, 'landed_canary_r71.jsonl'))}
B = {base(r['path']): r for r in jload(os.path.join(D, 'm71_canary.jsonl'))}
L = ['G2 canary product sha (byte-for-byte) landed -> m71', '=' * 70]
n = 0
for k in sorted(A):
    s, t = A[k]['sha'], B[k]['sha']
    same = 'SAME' if s == t else 'DIFF'
    n += same == 'SAME'
    L.append('%-28s %s -> %s  %s' % (k.split('@')[0], s, t, same))
L.append('')
L.append('G2 canary: SAME=%d/4  %s (quotation DIFF allowed only if its cf units turned green)'
         % (n, 'PASS' if n == 4 else 'CHECK'))
io.open(os.path.join(G, 'G2_canary_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G2] written SAME=%d' % n)

# ---------- G4p strict on div48 ----------
if os.path.isfile(os.path.join(D, 'strict_landed_r71.json')) and \
   os.path.isfile(os.path.join(D, 'strict_m71_r71.json')):
    A = {base(r['pyc']): r for r in json.load(io.open(os.path.join(D, 'strict_landed_r71.json'), encoding='utf-8'))}
    B = {base(r['pyc']): r for r in json.load(io.open(os.path.join(D, 'strict_m71_r71.json'), encoding='utf-8'))}
    L = ['G4p strict ruler on the 48 divergence targets (landed -> m71)', '=' * 70]
    ok_a = ok_b = da = db = 0
    for k in sorted(A):
        a, b = A[k], B[k]
        ca, cb = len(a['bad']), len(b['bad'])
        ok_a += a['ok']; ok_b += b['ok']; da += ca; db += cb
        v = 'SAME' if a == b else ('IMPROVED' if cb <= ca else 'REGRESSION')
        L.append('%-46s ok %3d/%-3d d=%-3d -> ok %3d/%-3d d=%-3d  %s'
                 % (k.split('@')[0], a['ok'], a['functions'], ca, b['ok'], b['functions'], cb, v))
    L.append('')
    L.append('STRICT TOTAL ok %d -> ok %d ; defects %d -> %d' % (ok_a, ok_b, da, db))
    io.open(os.path.join(G, 'G4p_strict_after_r71.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('[G4p] written ok %d -> %d, defects %d -> %d' % (ok_a, ok_b, da, db))
else:
    print('[G4p] strict jsons not ready; run sstrict67 on div48 for build_landed/build_m71 first')
