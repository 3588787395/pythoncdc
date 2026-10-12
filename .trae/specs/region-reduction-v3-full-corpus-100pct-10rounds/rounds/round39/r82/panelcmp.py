"""Panel byte-change census: which of the 20 panel products differ from the base run.

usage: python -X utf8 panelcmp.py <base-dir> <cand-dir>
"""
import os
import sys

SP = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/'
A, B = sys.argv[1], sys.argv[2]
rels = [x.strip() for x in open('D:/Temp/r82/PANEL_20files.txt', encoding='utf-8').read().split() if x.strip()]
changed = 0
missing = 0
for rel in rels:
    name = rel.replace('/', '_')[:-4] + '.py'
    pa, pb = os.path.join(A, name), os.path.join(B, name)
    if not (os.path.exists(pa) and os.path.exists(pb)):
        print('MISSING  %-60s base=%s cand=%s' % (rel, os.path.exists(pa), os.path.exists(pb)))
        missing += 1
        continue
    if open(pa, 'rb').read() != open(pb, 'rb').read():
        print('CHANGED  %-60s %d -> %d bytes' % (rel, os.path.getsize(pa), os.path.getsize(pb)))
        changed += 1
print('changed files = %d  (of %d panel files, missing=%d)' % (changed, len(rels), missing))
