# -*- coding: utf-8 -*-
"""Round 70 gate artifact generator (part 1): G0 / G1 / G2 canary."""
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
ROOT = r'D:/Temp/opencode/r70gate/center'
G = os.path.join(ROOT, 'logs')
D = os.path.join(ROOT, 'dump')


def jload(p):
    return [json.loads(l) for l in io.open(p, encoding='utf-8') if l.strip()]


def base(p):
    return p.replace('\\', '/').split('/')[-1] + '@' + p.replace('\\', '/').split('/')[-2]


# ---------- G0 ----------
pat = re.compile(r'region\.entry\s+in\s+\w+\.blocks')
L = ['G0 syntax / form gate (round 70, repository bytes after landing)', '=' * 70]
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
        py_compile.compile(p, cfile=os.path.join(tempfile.gettempdir(), 'g0a.pyc'), doraise=True)
        res = 'ast OK / py_compile OK'
    except Exception as e:
        res = 'FAIL %s' % e
        ok = False
    head = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + rel],
                          capture_output=True).stdout
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
io.open(os.path.join(G, 'G0_syntax_form_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G0] written')

# ---------- G1 ----------
A = {base(r['path']): r for r in jload(os.path.join(D, 'landed10_r70.jsonl'))}
B = {base(r['path']): r for r in jload(os.path.join(D, 'm70_10.jsonl'))}


def delta(m):
    try:
        return abs((m[1] or 0) - (m[2] or 0))
    except Exception:
        return 0


tally = {'IMPROVED': 0, 'SAME': 0, 'MOVED': 0, 'REGRESSION': 0, 'ERR': 0}
L = ['G1 official ruler on the 10 partial targets (landed -> m70)', '=' * 70]
cleared = []
for k in sorted(A):
    a, b = A[k], B[k]
    da, db = len(a['mism']), len(b['mism'])
    sa, sb = sum(delta(m) for m in a['mism']), sum(delta(m) for m in b['mism'])
    if db == 0 and da > 0:
        v = 'IMPROVED'
    elif db < da:
        v = 'IMPROVED'
    elif db > da:
        v = 'REGRESSION'
    elif a['mism'] == b['mism']:
        v = 'SAME'
    else:
        v = 'MOVED'
    tally[v] += 1
    if b.get('matched_functions') == b.get('total_functions'):
        cleared.append(k.split('/')[-1])
    L.append('%-46s %3d/%-3d d=%-3d |d|=%-4d -> %3d/%-3d d=%-3d |d|=%-4d  %s'
             % (k.split('/')[-1], a['matched_functions'], a['total_functions'], da, sa,
                b['matched_functions'], b['total_functions'], db, sb, v))
L.append('')
L.append('TALLY %s' % ' '.join('%s=%d' % kv for kv in sorted(tally.items())))
L.append('files fully cleared: %d (%s)' % (len(cleared), ', '.join(sorted(cleared))))
io.open(os.path.join(G, 'G1_targets_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G1] written', tally, 'cleared=%d' % len(cleared))

# ---------- G2 canary ----------
A = {base(r['path']): r for r in jload(os.path.join(D, 'landed_canary_r70.jsonl'))}
B = {base(r['path']): r for r in jload(os.path.join(D, 'm70_canary.jsonl'))}
L = ['G2 canary product sha (byte-for-byte) landed -> m70', '=' * 70]
n = 0
for k in sorted(A):
    s, t = A[k]['sha'], B[k]['sha']
    same = 'SAME' if s == t else 'DIFF'
    n += same == 'SAME'
    L.append('%-28s %s -> %s  %s' % (k.split('/')[-1], s, t, same))
L.append('')
L.append('G2 canary: SAME=%d/4  %s' % (n, 'PASS' if n == 4 else 'FAIL'))
io.open(os.path.join(G, 'G2_canary_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G2] written SAME=%d' % n)

# ---------- G2 strict canary ----------
for arm, name in (('head', 'head'), ('m70', 'm70')):
    d = json.load(io.open(os.path.join(D, 'strict_canary_%s.json' % arm), encoding='utf-8'))
    oka = sum(r['ok'] for r in d)
    fun = sum(r['functions'] for r in d)
    de = sum(len(r['bad']) for r in d)
    L = ['G2 strict ruler on the 4 canary targets (arm=%s)' % arm, '=' * 70]
    for r in d:
        L.append('%-28s strict %d/%d defects=%d' % (r['pyc'].split('/')[-1], r['ok'], r['functions'], len(r['bad'])))
    L.append('')
    L.append('STRICT TOTAL ok=%d/%d defects=%d' % (oka, fun, de))
    io.open(os.path.join(G, 'G2_strict_canary_%s_r70.txt' % arm), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G2s] written')

# ---------- G4p strict after ----------
A = {base(r['pyc']): r for r in json.load(io.open(os.path.join(D, 'strict_landed_r70.json'), encoding='utf-8'))}
B = {base(r['pyc']): r for r in json.load(io.open(os.path.join(D, 'strict_m70_r70.json'), encoding='utf-8'))}
L = ['G4p strict ruler on the 10 partial targets (landed -> m70)', '=' * 70]
ok_a = ok_b = da = db = 0
for k in sorted(A):
    a, b = A[k], B[k]
    ca, cb = len(a['bad']), len(b['bad'])
    ok_a += a['ok']; ok_b += b['ok']; da += ca; db += cb
    v = 'SAME' if a == b else ('IMPROVED' if cb <= ca else 'REGRESSION')
    L.append('%-46s ok %3d/%-3d d=%-3d -> ok %3d/%-3d d=%-3d  %s'
             % (k.split('/')[-1], a['ok'], a['functions'], ca, b['ok'], b['functions'], cb, v))
L.append('')
L.append('STRICT TOTAL ok %d/488 -> ok %d/488 ; defects %d -> %d' % (ok_a, ok_b, da, db))
io.open(os.path.join(G, 'G4p_strict_after_r70.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('[G4p] written ok %d -> %d, defects %d -> %d' % (ok_a, ok_b, da, db))
