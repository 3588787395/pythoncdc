# -*- coding: utf-8 -*-
"""Round 29 G0 helper: compile one synthetic repro to a 3.11.7 .pyc, measure it under every
arm asked for, and print the per-function signature (orig/decomp counts, jump/true diffs) plus
the first strict-ruler divergence of each mismatched function.

  python -X utf8 g0.py --src=<file.py> [--arms=landed,cand] [--out=<dir>]

Nothing here decides the verdict -- it only produces the measured evidence G0/G1 require,
in one command instead of four, and it never touches the repo index or the products.
"""
import importlib.util
import io
import json
import os
import py_compile
import subprocess
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r29gate'
HARNESS = os.path.join(ROOT, 'r29.py')
BS = chr(92)
MAGIC_3117 = bytes.fromhex('a70d0d0a')
sys.stdout.reconfigure(encoding='utf-8')

a = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
src = a['src']
arms = (a.get('arms', 'landed,cand')).split(',')
outdir = a.get('out', ROOT + '/g0')
if not os.path.isdir(outdir):
    os.makedirs(outdir)

dst_pyc = src[:-3] + '.pyc'
py_compile.compile(src, cfile=dst_pyc, doraise=True)
head = io.open(dst_pyc, 'rb').read(4)
assert head == MAGIC_3117, 'not a 3.11.7 pyc: %s' % head.hex()
print('compiled %s -> %s (magic %s)' % (os.path.basename(src), os.path.basename(dst_pyc), head.hex()))

lst = os.path.join(outdir, 'g0_list.txt')
io.open(lst, 'w', encoding='utf-8', newline='').write(dst_pyc.replace(BS, '/') + '\r\n')

recs = {}
for arm in arms:
    out = os.path.join(outdir, 'g0_%s.jsonl' % arm)
    if os.path.isfile(out):
        os.remove(out)
    r = subprocess.run([sys.executable, '-X', 'utf8', HARNESS, 'run',
                        '--arm=' + arm, '--list=' + lst, '--out=' + out],
                       capture_output=True, text=True, encoding='utf-8')
    assert os.path.isfile(out), 'arm %s produced nothing (rc=%s): %s' % (arm, r.returncode, (r.stderr or '')[-400:])
    rows = [json.loads(l) for l in io.open(out, encoding='utf-8') if l.strip()]
    assert len(rows) == 1, 'expected exactly one record, got %d' % len(rows)
    recs[arm] = rows[0]
    assert not rows[0].get('error'), 'decompile error on %s: %s' % (arm, rows[0]['error'])

_s = importlib.util.spec_from_file_location('r10', os.path.join(REPO, '_r10_strict_check.py'))
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)


def diverge(fn):
    orig = r10._load_map(dst_pyc)
    key = fn if fn in orig else [k for k in orig if k.endswith(fn)][0]
    ok = os.path.join(ROOT, 'build_landed',
                      os.path.basename(dst_pyc)[:-4] + 'OK.py').replace(BS, '/')
    for arm in arms:
        prod = os.path.join(ROOT, 'build_' + arm,
                            os.path.basename(dst_pyc)[:-4] + 'OK.py').replace(BS, '/')
        if not os.path.isfile(prod):
            continue
        dec = r10._compile_map(prod)
        o, d = r10.filtered(orig[key]), r10.filtered(dec[key])
        n = 0
        while n < min(len(o), len(d)) and o[n].opname == d[n].opname:
            n += 1
        print('  %s: orig=%d decomp=%d first divergence at #%d' % (arm, len(o), len(d), n))
        for k in range(max(0, n - 3), min(len(o), n + 6)):
            print('    o#%-4d %s' % (k, o[k].opname))
        print('     ---')
        for k in range(max(0, n - 3), min(len(d), n + 6)):
            print('    d#%-4d %s' % (k, d[k].opname))


for arm in arms:
    m = recs[arm]
    print('%-8s %s/%s  mism=%s' % (arm, m['matched_functions'], m['total_functions'], m['mism']))
base = recs[arms[0]]
for entry in (base.get('mism') or []):
    print('=== first divergence for %s' % entry[0])
    diverge(entry[0])
