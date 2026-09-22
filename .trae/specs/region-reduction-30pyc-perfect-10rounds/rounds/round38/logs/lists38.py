# -*- coding: utf-8 -*-
"""Round 38 battery-list builder: G2' reprobat51 + round-37 pins -> 59, G3 anchors106 + the
round-37 fully-matched target -> anchors107.

usage: python -X utf8 lists38.py
"""
import glob
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
M = r'D:/Temp/r38gate/r38m'
sys.stdout.reconfigure(encoding='utf-8')


def read(p):
    return [l.strip() for l in io.open(p, encoding='utf-8') if l.strip()]


b51 = read(M + '/reprobat51.txt')
pins = [p.replace('\\', '/').replace('/', os.sep)
        for p in sorted(glob.glob(REPO + os.sep + 'test_repros' + os.sep +
                                  'round37_ancestor_elif_or_arm' + os.sep + '*.pyc'))]
assert len(pins) == 8, len(pins)
# a pinned case is only reproducible while its source .py sits next to the .pyc (.gitignore drops pyc)
assert not [p for p in pins if not os.path.isfile(p[:-4] + '.py')], 'pinned source missing'
new = [p for p in pins if p not in b51]
out = b51 + new
io.open(M + '/reprobat59.txt', 'w', encoding='utf-8', newline='').write('\n'.join(out) + '\n')
print('reprobat59.txt = %d rows (51 previous + %d new round-37 pins)' % (len(out), len(new)))

a106 = read(M + '/anchors106.txt')
tgt = (REPO + '/site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc'
       ).replace('\\', '/').replace('/', os.sep)
print('strategy.pyc (round-37 target) already anchored: %s' % (tgt in a106))
a107 = a106 + ([tgt] if tgt not in a106 else [])
io.open(M + '/anchors107.txt', 'w', encoding='utf-8', newline='').write('\n'.join(a107) + '\n')
print('anchors107.txt = %d rows' % len(a107))
