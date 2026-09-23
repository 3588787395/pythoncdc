# -*- coding: utf-8 -*-
"""Round 53 archive asset: unified product diffs (landed-before vs R53-A arm) for every
file the G4 ruler says moved, so the archive shows the source-level change without
hand-editing any product."""
import difflib
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BS = chr(92)
FS = '/'
sys.stdout.reconfigure(encoding='utf-8')


def nm(p):
    q = p.replace(BS, FS)
    r0 = REPO.replace(BS, FS) + FS + 'site-packages' + FS
    if q.startswith(r0):
        q = q[len(r0):]
    return q.replace(FS, '__')[:-4].replace(':', '_') + 'OK.py'


os.makedirs('D:/Temp/r53gate/prod53', exist_ok=True)
total = 0
for p in [l.strip() for l in io.open('D:/Temp/r53gate/g4affected53.txt', encoding='utf-8') if l.strip()]:
    f = nm(p)
    a = io.open('D:/Temp/r53gate/build_landed/' + f, encoding='utf-8').read().splitlines()
    b = io.open('D:/Temp/r53gate/build_c53a/' + f, encoding='utf-8').read().splitlines()
    d = list(difflib.unified_diff(a, b, fromfile='before/' + f, tofile='r53a/' + f, lineterm='', n=1))
    dst = 'D:/Temp/r53gate/prod53/' + f[:-5] + '.diff'
    io.open(dst, 'w', encoding='utf-8', newline='\n').write('\n'.join(d) + '\n')
    total += len(d)
    print('%-56s diff=%d lines' % (os.path.basename(dst)[:56], len(d)))
print('total diff lines %d over %d files' % (total, len(open('D:/Temp/r53gate/g4affected53.txt').read().split())))
