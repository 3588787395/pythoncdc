import io
import json
import os
import shutil
import sys

ARCH = r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round31/logs'
DST = r'D:/Temp/r32gate/c1'
REPO = r'F:/Downloads/pythoncdc-main'
SEP = chr(92)

sys.stdout.reconfigure(encoding='utf-8')
if not os.path.isdir(DST):
    os.makedirs(DST)

t = io.open(os.path.join(ARCH, 'r31c.py'), encoding='utf-8', newline='').read()
assert t.count('D:/Temp/r31gate/c1') == 1, t.count('D:/Temp/r31gate/c1')
t2 = t.replace('D:/Temp/r31gate/c1', 'D:/Temp/r32gate/c1')
assert t2.count('D:/Temp/r32gate/c1') == 1
io.open(os.path.join(DST, 'r32c.py'), 'w', encoding='utf-8', newline='').write(t2)

g = io.open(os.path.join(ARCH, 'g4prime31.py'), encoding='utf-8', newline='').read()
io.open(os.path.join(DST, 'g4prime32.py'), 'w', encoding='utf-8', newline='').write(g)

rows = [l.rstrip('\r\n') for l in io.open(r'D:/Temp/r32gate/pool32.txt', encoding='utf-8')]
assert rows[0].startswith('baseline(landed round31 index, HEAD '), rows[0]
d1 = [l.split()[0] for l in rows if l.startswith('  ') and l.rstrip().endswith('deficit 1')]
assert len(d1) == 7, len(d1)
assert all(p.endswith('.pyc') for p in d1), d1
io.open(DST + '/d1list.txt', 'w', encoding='utf-8', newline='').write('\n'.join(d1) + '\n')

idx = json.load(io.open(REPO + SEP + 'pyc_index.json', encoding='utf-8'))
assert len(idx) == 402, len(idx)
assert all(e['path'].startswith(REPO.replace(SEP, '/') + '/site-packages/') for e in idx)
allp = sorted(e['path'] for e in idx)
assert len(allp) == 402, len(allp)
missing = [p for p in allp if not os.path.isfile(p.replace('/', SEP))]
assert not missing, missing[:3]
prev = [l.rstrip('\r\n') for l in io.open(r'D:/Temp/r31gate/all402.txt', encoding='utf-8') if l.strip()]
assert prev == allp, 'corpus set drifted from round 31 (%d vs %d)' % (len(prev), len(allp))
io.open(DST + '/all402.txt', 'w', encoding='utf-8', newline='').write('\n'.join(allp) + '\n')

# load-bearing battery: 98 anchors + round-31 witness + round-31 control
a98 = [l.rstrip('\r\n') for l in io.open(os.path.join(ARCH, 'anchors98.txt'), encoding='utf-8') if l.strip()]
assert len(a98) == 98, len(a98)
r31 = [REPO + '/test_repros/round31_arm_terminal_join/r31a_witness.pyc',
       REPO + '/test_repros/round31_arm_terminal_join/r31a_control.pyc']
for p in r31:
    assert os.path.isfile(p.replace('/', SEP)), 'missing %s' % p
a100 = a98 + r31
assert len(set(a100)) == 100, len(set(a100))
io.open(DST + '/anchors100.txt', 'w', encoding='utf-8', newline='').write('\n'.join(a100) + '\n')
io.open(r'D:/Temp/r32gate/anchors100.txt', 'w', encoding='utf-8', newline='').write('\n'.join(a100) + '\n')

# G2' battery (38 previous-round synthetic repros) + the count comparator, both path-generic
def _ensure_pyc(paths):
    """Synthetic repros' .pyc are gitignored: regenerate from the tracked .py with an explicit
    cfile (the proven round-31 recipe) whenever one is absent."""
    import py_compile
    for p in paths:
        q = p.replace('/', SEP)
        if not os.path.isfile(q):
            src = q[:-4] + '.py'
            assert os.path.isfile(src), 'neither %s nor %s exists' % (q, src)
            py_compile.compile(src, cfile=q, doraise=True)
            assert os.path.isfile(q), 'py_compile wrote no bytes for %s' % src


bat = [l.rstrip('\r\n') for l in io.open(os.path.join(ARCH, 'reprobat38.txt'), encoding='utf-8') if l.strip()]
assert len(bat) == 38, len(bat)
_ensure_pyc(bat)
_ensure_pyc(a100)
io.open(r'D:/Temp/r32gate/reprobat38.txt', 'w', encoding='utf-8', newline='').write('\n'.join(bat) + '\n')
shutil.copyfile(os.path.join(ARCH, 'cmp30.py'), r'D:/Temp/r32gate/cmp30.py')
print('setup ok: harness forked, d1list=%d all402=%d anchors100=%d (98 + 2 round31) reprobat38=%d'
      % (len(d1), len(allp), len(a100), len(bat)))
