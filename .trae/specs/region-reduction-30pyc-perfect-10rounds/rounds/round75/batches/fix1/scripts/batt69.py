# -*- coding: utf-8 -*-
"""fix1: closeout69 battery gate with resumable arm runs (each h62 invocation <300s).

Faithful to `closeout69.py battery landed <arm>`: same repro_list(), same run_arm(),
same per-repro table + `candidate columns worse-than-landed on N repro(s)` verdict.
Difference: the per-arm h62 run is chunked (budget=240) and NEVER deletes an
already-complete jsonl, so the whole gate stays under the 300s-per-command rule.
"""
import importlib.util as iu
import io
import json
import os
import subprocess
import sys

CEN = r'D:/Temp/opencode/r75gate/center'
sys.stdout.reconfigure(encoding='utf-8')

_sp = iu.spec_from_file_location('co69', os.path.join(CEN, 'closeout69.py'))
co69 = iu.module_from_spec(_sp)
_sp.loader.exec_module(co69)

paths = co69.repro_list()
print('repro pycs: %d (round63-69 batches + %d pinned R62 witnesses)'
      % (len(paths), len(co69.PINNED)))
assert paths
lf = os.path.join(CEN, 'dump', 'reprolist65.txt')
io.open(lf, 'w', encoding='utf-8', newline='\n').write('\n'.join(paths) + '\n')

arms = sys.argv[1:] or ['landed', 'jqop1']
res = {}
for arm in arms:
    out = os.path.join(CEN, 'dump', 'repro65_%s.jsonl' % arm)
    for _round in range(12):
        done = set()
        if os.path.isfile(out):
            for l in io.open(out, encoding='utf-8'):
                if l.strip():
                    try:
                        r = json.loads(l)
                    except Exception:
                        continue
                    done.add(r['path'].replace('\\', '/'))
        if len(done) >= len(paths):
            break
        print('[%s] round%d: %d/%d done, running h62...' % (arm, _round, len(done), len(paths)))
        sys.stdout.flush()
        cmd = [sys.executable, '-X', 'utf8', os.path.join(CEN, 'h62.py'), 'run',
               '--arm=%s' % arm, '--list=dump/reprolist65.txt',
               '--out=dump/repro65_%s.jsonl' % arm, '--budget=240']
        p = subprocess.run(cmd, cwd=CEN, capture_output=True, text=True,
                           timeout=295, errors='replace')
        tail = (p.stdout or '').strip().split('\n')[-1:]
        print('   rc=%s %s' % (p.returncode, tail[0][:160] if tail else ''))
        sys.stdout.flush()
    rows = {}
    for l in io.open(out, encoding='utf-8'):
        if l.strip():
            try:
                r = json.loads(l)
            except Exception:
                continue
            rows[r['path'].replace('\\', '/')] = r
    res[arm] = rows
    print('[%s] records=%d' % (arm, len(rows)))

print('%-62s %s' % ('repro', '  '.join('%-22s' % a for a in arms)))
worst = 0
for pth in paths:
    cells = []
    for arm in arms:
        r = res[arm].get(pth)
        if r is None:
            cells.append('%-22s' % 'NO-RECORD')
        elif r.get('error'):
            cells.append('%-22s' % ('ERR ' + r['error'][:16]))
        else:
            bad = len(r['mism'] or [])
            delta = sum((m[2] or 0) - (m[1] or 0) for m in (r['mism'] or []))
            cells.append('%-22s' % ('%d/%d bad=%d d=%+d'
                                    % (r['matched_functions'], r['total_functions'], bad, delta)))
            if arm != arms[0] and (r['matched_functions']
                                   < (res[arms[0]].get(pth) or {}).get('matched_functions', 0)):
                worst += 1
    key = pth.replace('\\', '/')
    label = key.split('test_repros/')[-1] if 'test_repros/' in key else os.path.basename(key)
    print('%-62s %s' % (label, '  '.join(cells)))
print('candidate columns worse-than-landed on %d repro(s)' % worst)
