# -*- coding: utf-8 -*-
"""count occurrences of a literal anchor (LF-normalised) in a repo core file"""
import io
import sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main/'
rel, anchor = sys.argv[1], sys.argv[2]
if anchor.startswith('@file:'):
    anchor = io.open(anchor[6:], encoding='utf-8').read()
src = io.open(REPO + rel, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
print('rel=%s anchor_len=%d occurrences=%d' % (rel, len(anchor), src.count(anchor)))
i = src.find(anchor)
while i >= 0:
    print('  at char %d (line %d)' % (i, src[:i].count('\n') + 1))
    i = src.find(anchor, i + 1)
