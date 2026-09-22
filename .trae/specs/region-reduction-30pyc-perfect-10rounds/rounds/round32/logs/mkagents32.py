# -*- coding: utf-8 -*-
"""Round 32 diagnosis-line scratch roots: give each diagnose-only agent a private copy of the
mirror harness whose ROOT literal points at its own directory (no shared write targets), plus the
measurement lists it needs.  The agent may only ever write inside its own root.

  python -X utf8 mkagents32.py A B
"""
import io
import os
import shutil
import sys

BASE = r'D:/Temp/r32gate'
ARCH = r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round31/logs'
SEP = chr(92)
sys.stdout.reconfigure(encoding='utf-8')

harness = io.open(BASE + '/c1/r32c.py', encoding='utf-8', newline='').read()
assert harness.count('D:/Temp/r32gate/c1') == 1

for tag in sys.argv[1:]:
    assert tag in 'ABCDEF', tag
    dst = '%s/%s' % (BASE, tag)
    if not os.path.isdir(dst):
        os.makedirs(dst)
    h = harness.replace('D:/Temp/r32gate/c1', 'D:/Temp/r32gate/' + tag)
    assert h.count('D:/Temp/r32gate/' + tag) == 1 and 'r32gate/c1' not in h
    io.open(dst + '/r32c_%s.py' % tag, 'w', encoding='utf-8', newline='').write(h)
    shutil.copyfile(BASE + '/c1/g4prime32.py', dst + '/g4prime32.py')
    shutil.copyfile(BASE + '/cmp30.py', dst + '/cmp30.py')
    for l in ('d1list.txt', 'all402.txt', 'anchors100.txt', 'reprobat38.txt'):
        shutil.copyfile(BASE + '/c1/' + l if os.path.isfile(BASE + '/c1/' + l) else BASE + '/' + l,
                        dst + '/' + l)
    for sub in ('mirr_head', 'mirr_c', 'mirr_landed'):
        p = dst + '/' + sub
        if not os.path.isdir(p):
            os.makedirs(p)
    print('%s ready: %s' % (tag, dst))
