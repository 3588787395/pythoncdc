# -*- coding: utf-8 -*-
"""Round 34 scratch root: fork the mirror harness onto the landed bytes (commit 762e8213, core
sha 2d3a5d51d114da77d3d4), rebuild the target lists and grow the load-bearing battery to
anchors104 = anchors102 + the round-33 witness + this round's landed target IQCommon/utils.pyc.

  python -X utf8 setup34.py
"""
import io
import json
import os
import shutil
import sys

REPO = r'F:/Downloads/pythoncdc-main'
SEP = chr(92)
A33 = REPO + SEP + '.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round33/logs'.replace('/', SEP)
A31 = REPO + SEP + '.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round31/logs'.replace('/', SEP)
DST = r'D:/Temp/r34gate/r34'
sys.stdout.reconfigure(encoding='utf-8')
if not os.path.isdir(DST):
    os.makedirs(DST)


def rd(p):
    b = io.open(p, 'rb').read()
    assert len(b) > 0, 'empty source %s' % p
    return b.decode('utf-8-sig').replace('\r\n', '\n')


def wr(p, text):
    io.open(p, 'w', encoding='utf-8', newline='').write(text.replace('\n', '\r\n'))


# ---- harness fork: only the scratch root may differ --------------------------------------
t = rd(A33 + SEP + 'tool_r33c.py')
assert t.count('D:/Temp/r33gate/c33') == 1, t.count('D:/Temp/r33gate/c33')
t2 = t.replace('D:/Temp/r33gate/c33', 'D:/Temp/r34gate/r34')
assert t2.count('D:/Temp/r34gate/r34') == 1 and 'r33gate' not in t2
wr(DST + '/r34c.py', t2)
for n in ('g4prime33.py', 'hunks33.py', 'dump33.py', 'probe_chain.py'):
    wr(DST + '/' + n.replace('33', '34'), rd(A33 + SEP + 'tool_' + n))
wr(r'D:/Temp/r34gate/pycache_probe34.py', rd(A33 + SEP + 'tool_pycache_probe33.py'))

# ---- mirrors must not inherit cached bytecode (round-33 line C) --------------------------
assert "ignore_patterns('__pycache__')" in t2 and "assert not [d for d, _, _ in os.walk" in t2, \
    'harness fork lost the __pycache__ guard'


def _ensure_pyc(paths):
    import py_compile
    for p in paths:
        q = p.replace('/', SEP)
        if not os.path.isfile(q):
            src = q[:-4] + '.py'
            assert os.path.isfile(src), 'neither %s nor %s exists' % (q, src)
            py_compile.compile(src, cfile=q, doraise=True)
            assert os.path.isfile(q), 'py_compile wrote no bytes for %s' % src


new = [REPO.replace(SEP, '/') + '/test_repros/round33_return_through_statement/r33a_witness.pyc',
       REPO.replace(SEP, '/') + '/site-packages/IQCommon/utils.pyc']
_ensure_pyc(new)
for p in new:
    assert os.path.getsize(p.replace('/', SEP)) > 0, 'empty pyc %s' % p

# ---- target lists from the pool measured this round --------------------------------------
rows = [l.rstrip('\r\n') for l in io.open(r'D:/Temp/r34gate/pool34.txt', encoding='utf-8')]
assert rows[0].startswith('baseline(landed round33 index, HEAD'), rows[0]
d1 = [l.split()[0] for l in rows if l.startswith('  ') and l.rstrip().endswith('deficit 1')]
d2 = [l.split()[0] for l in rows if l.startswith('  ') and l.rstrip().endswith('deficit 2')]
assert len(d1) == 7 and len(d2) == 12, (len(d1), len(d2))
assert all(p.endswith('.pyc') for p in d1 + d2)
wr(DST + '/d1list.txt', '\n'.join(d1) + '\n')
wr(DST + '/d2list.txt', '\n'.join(d2) + '\n')

idx = json.load(io.open(REPO + SEP + 'pyc_index.json', encoding='utf-8'))
assert len(idx) == 402, len(idx)
allp = sorted(e['path'] for e in idx)
assert all(os.path.isfile(p.replace('/', SEP)) for p in allp)
prev = [l.rstrip('\r\n') for l in io.open(A33 + SEP + 'list_all402.txt', encoding='utf-8') if l.strip()]
assert prev == allp, 'corpus set drifted from round 33 (%d vs %d)' % (len(prev), len(allp))
wr(DST + '/all402.txt', '\n'.join(allp) + '\n')

# ---- load-bearing battery: anchors102 (rebuilt from its own sources) + 2 = 104 -----------
a98 = [l.rstrip('\r\n') for l in io.open(A31 + SEP + 'anchors98.txt', encoding='utf-8') if l.strip()]
assert len(a98) == 98, len(a98)
r31 = [REPO.replace(SEP, '/') + '/test_repros/round31_arm_terminal_join/r31a_witness.pyc',
       REPO.replace(SEP, '/') + '/test_repros/round31_arm_terminal_join/r31a_control.pyc']
r32 = [REPO.replace(SEP, '/') + '/test_repros/round32_pop_stmt_terminator/r32c_witness.pyc',
       REPO.replace(SEP, '/') + '/test_repros/round32_pop_stmt_terminator/r32c_repro.pyc']
_ensure_pyc(r31 + r32)
a102 = a98 + r31 + r32
assert len(set(a102)) == 102, len(set(a102))
sc = [l.rstrip('\r\n') for l in io.open(A33 + SEP + 'list_anchors102.txt', encoding='utf-8') if l.strip()]
assert sc == a102, 'anchors102 rebuilt != round-33 archived copy'
a104 = a102 + new
assert len(set(a104)) == 104, len(set(a104))
wr(DST + '/anchors104.txt', '\n'.join(a104) + '\n')

# ---- previous-round synthetic repro battery: 38 + the round-33 witness = 39 --------------
bat = [l.rstrip('\r\n') for l in io.open(A31 + SEP + 'reprobat38.txt', encoding='utf-8') if l.strip()]
assert len(bat) == 38, len(bat)
prev_bat = [l.rstrip('\r\n') for l in io.open(A33 + SEP + 'list_reprobat38.txt', encoding='utf-8') if l.strip()]
assert prev_bat == bat, 'reprobat38 rebuilt != round-33 archived copy'
b39 = bat + [new[0]]
assert len(set(b39)) == 39, len(set(b39))
_ensure_pyc(b39)
_ensure_pyc(a104)
wr(r'D:/Temp/r34gate/reprobat39.txt', '\n'.join(b39) + '\n')
print('setup34 ok: harness forked; d1list=%d d2list=%d all402=%d anchors104=%d reprobat39=%d'
      % (len(d1), len(d2), len(allp), len(a104), len(b39)))
