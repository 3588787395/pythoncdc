# -*- coding: utf-8 -*-
"""Round 33 scratch root: fork the mirror harness onto the landed bytes (commit 910a8f74, core
sha fa43dbc9e878eeacbfe0), rebuild the target lists and the load-bearing battery
(anchors102 = anchors100 + the two round-32 synthetic files).

  python -X utf8 setup33.py
"""
import io
import json
import os
import shutil
import sys

REPO = r'F:/Downloads/pythoncdc-main'
SEP = chr(92)
ARCH = REPO + SEP + '.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round32/logs'.replace('/', SEP)
DST = r'D:/Temp/r33gate/c33'
sys.stdout.reconfigure(encoding='utf-8')
if not os.path.isdir(DST):
    os.makedirs(DST)

# ---- harness fork: only the scratch root may differ --------------------------------------
t = io.open(os.path.join(ARCH, 'r32c.py'), encoding='utf-8', newline='').read()
assert t.count('D:/Temp/r32gate/c1') == 1, t.count('D:/Temp/r32gate/c1')
t2 = t.replace('D:/Temp/r32gate/c1', 'D:/Temp/r33gate/c33')
assert t2.count('D:/Temp/r33gate/c33') == 1 and 'r32gate/c1' not in t2
io.open(DST + '/r33c.py', 'w', encoding='utf-8', newline='').write(t2)
for n in ('g4prime32.py', 'hunks32.py', 'dump32.py'):
    shutil.copyfile(os.path.join(ARCH, n), os.path.join(DST, n.replace('32', '33')))
shutil.copyfile(os.path.join(ARCH, 'cmp30.py'), r'D:/Temp/r33gate/cmp30.py')

# ---- round-32 synthetic repros must exist as .pyc for the battery -------------------------
R32 = REPO + SEP + 'test_repros/round32_pop_stmt_terminator'.replace('/', SEP)
witness_src = r'D:/Temp/r32gate/c1/r32c_witness.py'
witness_dst = R32 + SEP + 'r32c_witness.py'
if not os.path.isfile(witness_dst):
    shutil.copyfile(witness_src, witness_dst)
    print('promoted round-32 witness into the tracked repro dir')
assert os.path.isfile(witness_dst)


def _ensure_pyc(paths):
    import py_compile
    for p in paths:
        q = p.replace('/', SEP)
        if not os.path.isfile(q):
            src = q[:-4] + '.py'
            assert os.path.isfile(src), 'neither %s nor %s exists' % (q, src)
            py_compile.compile(src, cfile=q, doraise=True)
            assert os.path.isfile(q), 'py_compile wrote no bytes for %s' % src


new = [REPO.replace(SEP, '/') + '/test_repros/round32_pop_stmt_terminator/r32c_witness.pyc',
       REPO.replace(SEP, '/') + '/test_repros/round32_pop_stmt_terminator/r32c_repro.pyc']
_ensure_pyc(new)
assert os.path.getsize(new[0].replace('/', SEP)) > 0 and os.path.getsize(new[1].replace('/', SEP)) > 0

# ---- target lists from the pool measured this round --------------------------------------
rows = [l.rstrip('\r\n') for l in io.open(r'D:/Temp/r33gate/pool33.txt', encoding='utf-8')]
assert rows[0].startswith('baseline(landed round32 index, HEAD 910a8f74'), rows[0]
d1 = [l.split()[0] for l in rows if l.startswith('  ') and l.rstrip().endswith('deficit 1')]
d2 = [l.split()[0] for l in rows if l.startswith('  ') and l.rstrip().endswith('deficit 2')]
assert len(d1) == 8 and len(d2) == 12, (len(d1), len(d2))
assert all(p.endswith('.pyc') for p in d1 + d2)
io.open(DST + '/d1list.txt', 'w', encoding='utf-8', newline='').write('\n'.join(d1) + '\n')
io.open(DST + '/d2list.txt', 'w', encoding='utf-8', newline='').write('\n'.join(d2) + '\n')

idx = json.load(io.open(REPO + SEP + 'pyc_index.json', encoding='utf-8'))
assert len(idx) == 402, len(idx)
allp = sorted(e['path'] for e in idx)
assert all(os.path.isfile(p.replace('/', SEP)) for p in allp)
prev = [l.rstrip('\r\n') for l in io.open(os.path.join(ARCH, 'all402.txt'), encoding='utf-8') if l.strip()] \
    if os.path.isfile(os.path.join(ARCH, 'all402.txt')) else None
if prev is None:
    prev = [l.rstrip('\r\n') for l in io.open(r'D:/Temp/r32gate/c1/all402.txt', encoding='utf-8') if l.strip()]
assert prev == allp, 'corpus set drifted from round 32 (%d vs %d)' % (len(prev), len(allp))
io.open(DST + '/all402.txt', 'w', encoding='utf-8', newline='').write('\n'.join(allp) + '\n')

# ---- load-bearing battery: anchors100 + the two round-32 files = 102 ---------------------
# anchors100 itself is rebuilt from its own sources (round-31 archive 98 + round-31 witness and
# control) rather than trusted from scratch, then cross-checked against scratch if present.
ARCH31 = REPO + SEP + '.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round31/logs'.replace('/', SEP)
a98 = [l.rstrip('\r\n') for l in io.open(os.path.join(ARCH31, 'anchors98.txt'), encoding='utf-8') if l.strip()]
assert len(a98) == 98, len(a98)
r31 = [REPO.replace(SEP, '/') + '/test_repros/round31_arm_terminal_join/r31a_witness.pyc',
       REPO.replace(SEP, '/') + '/test_repros/round31_arm_terminal_join/r31a_control.pyc']
_ensure_pyc(r31)
a100 = a98 + r31
assert len(set(a100)) == 100, len(set(a100))
sc = r'D:/Temp/r32gate/c1/anchors100.txt'
if os.path.isfile(sc):
    same = [l.rstrip('\r\n') for l in io.open(sc, encoding='utf-8') if l.strip()]
    assert same == a100, 'anchors100 rebuilt != round-32 scratch copy'
a102 = a100 + new
assert len(set(a102)) == 102, len(set(a102))
io.open(DST + '/anchors102.txt', 'w', encoding='utf-8', newline='').write('\n'.join(a102) + '\n')
io.open(r'D:/Temp/r33gate/anchors102.txt', 'w', encoding='utf-8', newline='').write('\n'.join(a102) + '\n')

bat = [l.rstrip('\r\n') for l in io.open(os.path.join(ARCH31, 'reprobat38.txt'), encoding='utf-8') if l.strip()]
assert len(bat) == 38, len(bat)
_ensure_pyc(bat)
_ensure_pyc(a102)
io.open(r'D:/Temp/r33gate/reprobat38.txt', 'w', encoding='utf-8', newline='').write('\n'.join(bat) + '\n')
print('setup33 ok: harness forked; d1list=%d d2list=%d all402=%d anchors102=%d reprobat38=%d'
      % (len(d1), len(d2), len(allp), len(a102), len(bat)))
