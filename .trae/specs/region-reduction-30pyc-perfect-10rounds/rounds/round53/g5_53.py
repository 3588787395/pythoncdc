# -*- coding: utf-8 -*-
"""G5 for Round 53: the landed core must reproduce the gated arm products byte-for-byte,
and only then may a shipped *OK.py be refreshed (products are never hand-edited).

usage: python -X utf8 g5_53.py <arm-build-dir> <affected-pyc-list>
  <affected-pyc-list>: absolute pyc paths, one per line (the G4 MOVED/IMPROVED set).
Also runs the two canaries: fly/data/quotation.pyc (official + strict) and the
test_repros/round16_sink battery against the SHIPPED products.
"""
import hashlib
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r53gate'
sys.stdout.reconfigure(encoding='utf-8')
ARM_DIR = os.path.abspath(sys.argv[1])
LIST = sys.argv[2]
sys.path.insert(0, REPO)
_s = importlib.util.spec_from_file_location('r53sc', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)
_s2 = importlib.util.spec_from_file_location('pbv53', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_s2)
_s2.loader.exec_module(pbv)
import pycdc
assert os.path.abspath(pycdc.__file__).replace('\\', '/').startswith(REPO.replace('\\', '/')), \
    'pycdc did not resolve to the worktree core'
print('pycdc = %s' % os.path.abspath(pycdc.__file__))
SHA = lambda b: hashlib.sha256(b).hexdigest()[:16]


def armname(p):
    q = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if q.startswith(r0):
        q = q[len(r0):]
    return q.replace('/', '__')[:-4].replace(':', '_') + 'OK.py'


paths = [l.strip() for l in io.open(LIST, encoding='utf-8') if l.strip()]
n_ident = 0
for p in paths:
    pyc = os.path.abspath(p.replace('/', os.sep))
    txt = pycdc.decompile_pyc(pyc)
    arm_path = os.path.join(ARM_DIR, armname(p))
    arm_txt = io.open(arm_path, encoding='utf-8').read()
    same = txt == arm_txt
    n_ident += same
    if same:
        with io.open(pyc[:-4] + 'OK.py', 'w', encoding='utf-8') as f:
            f.write(txt)
    print('%-62s arm-identical=%-5s refreshed=%s  sha %s/%s'
          % (pyc.replace(REPO.replace('\\', '/') + '/', '')[-62:], same, same,
             SHA(txt.encode('utf-8')), SHA(arm_txt.encode('utf-8'))))
    if not same:
        print('   !! landed %d B vs arm %d B' % (len(txt), len(arm_txt)))
print('landed-vs-arm identical: %d/%d' % (n_ident, len(paths)))

print('---- canary quotation.pyc ----')
q = os.path.abspath(REPO + '/site-packages/fly/data/quotation.pyc')
txt = pycdc.decompile_pyc(q)
qp = ROOT + '/g5_quotation.py'
io.open(qp, 'w', encoding='utf-8', newline='').write(txt)
r = pbv.bytecode_diff(q, qp)
print('official %s/%s' % (r.get('matched_functions'), r.get('total_functions')))
o = r10._load_map(q)
d = r10._compile_map(qp)
bad = [n for n in sorted(set(o) & set(d)) if r10.strict_compare(o[n], d[n])[2]]
print('strict  %d/%d' % (len(set(o) & set(d)) - len(bad), len(set(o) & set(d))))
for b in bad:
    print('    ' + b)

print('---- canary round16_sink (shipped products) ----')
import glob
sink = sorted(glob.glob(os.path.join(REPO, 'test_repros/round16_sink/*.pyc')))
n_match = n_bad = 0
for pyc in sink:
    prod = pyc[:-4] + 'OK.py'
    if not os.path.exists(prod):
        print('  MISSING PRODUCT %s' % os.path.basename(pyc))
        n_bad += 1
        continue
    o = r10._load_map(pyc)
    d = r10._compile_map(prod)
    bad = [n for n in sorted(set(o) & set(d)) if r10.strict_compare(o[n], d[n])[2]]
    if bad or set(o) != set(d):
        n_bad += 1
        print('  MISMATCH %s %s' % (os.path.basename(pyc), bad))
    else:
        n_match += 1
print('round16_sink: MATCH=%d BAD=%d of %d' % (n_match, n_bad, len(sink)))
