# -*- coding: utf-8 -*-
"""Round 74: G4 (official 402 totals), G8 re-read with correct encoding, Land74 replay
from HEAD bytes (proves the landed bytes == the measured m74 spec, not a hand edit)."""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
C = r'D:/Temp/opencode/r74gate/center'
G = os.path.join(C, 'logs')
D = os.path.join(C, 'dump')
BS = os.sep


def read_any(p):
    raw = io.open(p, 'rb').read()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return raw.decode('utf-16')
    if raw[:3] == b'\xef\xbb\xbf':
        return raw.decode('utf-8-sig')
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return raw.decode('utf-16')


# ---------- G4 ----------
txt = read_any(os.path.join(D, 'G3_batch_r74.txt'))
m = re.search(r'total_pyc:\s+(\d+)', txt)
g = dict(re.findall(r'(total_pyc|verified_pyc|ok_pyc|partial_pyc|failed_pyc|'
                    r'total_functions|matched_functions|cumulative_match_rate):\s+(\S+)', txt))
L = ['G4 official ruler stats (scripts/pyc_batch_verify.py, round 74)', '=' * 70,
     'total  %s / verified %s / ok %s / partial %s / failed %s'
     % (g.get('total_pyc'), g.get('verified_pyc'), g.get('ok_pyc'),
        g.get('partial_pyc'), g.get('failed_pyc')),
     '%s/%s = %s  (round73 5717/5746 = 99.50%%)'
     % (g.get('matched_functions'), g.get('total_functions'), g.get('cumulative_match_rate')),
     'Traceback=%d FAIL-line=%d' % (txt.count('Traceback'), len(re.findall(r'^FAIL', txt, re.M))),
     'G4 verdict: %s' % ('PASS' if g.get('failed_pyc') == '0' and
                         g.get('cumulative_match_rate', '') >= '99.50%' else 'CHECK')]
io.open(os.path.join(G, 'G4_stats_r74.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('[G4]', L[2], L[3], L[-1])

# ---------- Land73 replay (from HEAD bytes) ----------
CR = chr(13)
L = ['Land74 replay check: HEAD(R73) bytes + m74 spec  ==  worktree(R74) bytes', '=' * 70]
ok = True
for spec_name in ('m74_region_ast_generator.py.json', 'm74_region_analyzer.py.json'):
    spec = json.load(io.open(os.path.join(r'D:/Temp/opencode/r74gate', spec_name), encoding='utf-8'))
    rel = spec['file']
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    head = subprocess.run(['git', '-C', REPO, 'show', 'HEAD:' + rel],
                          capture_output=True).stdout
    head_bom = head[:3] == b'\xef\xbb\xbf'
    u = head.decode('utf-8-sig').replace(CR, '\n')
    patched = u
    hits = []
    for e in edits:
        hits.append(patched.count(e['anchor']))
        patched = patched.replace(e['anchor'], e['repl'])
    work = io.open(os.path.join(REPO, rel.replace('/', BS)), 'rb').read()
    work_bom = work[:3] == b'\xef\xbb\xbf'
    nl = '\r\n' if work.decode('utf-8-sig').count(CR) else '\n'
    out = patched.replace('\n', nl).encode('utf-8')
    if work_bom:
        out = b'\xef\xbb\xbf' + out
    same = out == work
    ok &= same and all(h == 1 for h in hits) and work_bom == head_bom
    L.append('%-34s edits=%d anchor-hits=%s' % (rel, len(edits), hits))
    L.append('   HEAD %d B -> worktree %d B ; BOM %s -> %s ; nl=%s ; replay==worktree: %s'
             % (len(head), len(work), head_bom, work_bom,
                'CRLF' if nl == CR + '\n' else 'LF', same))
    ins = sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in edits)
    L.append('   net inserted lines (spec, LF) %+d' % ins)
L += ['', 'Land73 replay verdict: %s' % ('PASS' if ok else 'FAIL')]
io.open(os.path.join(G, 'Land74_replay_r74.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('[replay]', L[-1])

# ---------- G8 re-read ----------
import py_compile
import tempfile
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
        py_compile.compile(prod, cfile=os.path.join(tempfile.gettempdir(), 'g873.pyc'), doraise=True)
    except Exception:
        bad += 1
L = ['G8 artifacts (402 shipped *OK.py)', '=' * 70,
     'products=%d missing=%d py_compile bad=%d' % (len(ents), missing, bad),
     'G3 batch log: Traceback=%d FAIL-line=%d' % (txt.count('Traceback'),
                                                  len(re.findall(r'^FAIL', txt, re.M))),
     'G8 verdict: %s' % ('PASS' if missing == 0 and bad == 0 and
                         txt.count('Traceback') == 0 else 'FAIL')]
io.open(os.path.join(G, 'G8_artifacts_r74.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print('[G8]', L[2], L[3], L[4])
