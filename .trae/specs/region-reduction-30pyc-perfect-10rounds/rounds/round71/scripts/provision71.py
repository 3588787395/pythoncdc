# -*- coding: utf-8 -*-
"""Round 71 step 0: provision diag1 (test engineer) and fix1 (fix engineer) workspaces
from the proven r70gate centre instruments, retargeting only workspace-root string
literals (r70gate -> r71gate).  Nothing is executed; no repository file is touched."""
import io
import os
import shutil
import sys

SRC = r'D:/Temp/opencode/r70gate/center'
RT = r'D:/Temp/opencode/r71gate'
sys.stdout.reconfigure(encoding='utf-8')

PY_FILES = ['h62.py', 'align.py', 'regdump.py', 'disf.py', 'nhunks.py', 'cstrict.py',
            'cstrict67.py', 'sstrict67.py', 'strict_repo67.py', 'closeout69.py',
            'battable67.py', 'dumpfn.py', 'mk_spec.py', 'probe_chain.py', 'blast67.py',
            'audit5_g5_67.py', 'nested_diff.py']
CHAIN = {'mbuild70.py': 'mbuild71.py', 'mkfinal70.py': 'mkfinal71.py',
         'land70.py': 'land71.py', 'cadelta70.py': 'cadelta71.py',
         'mk_spec.py': 'mk_spec71.py'}
TXT_FILES = ['battery.txt', 'canary.txt', 'shapes_r63.txt', 'all402.txt', 'all16.txt',
             'targets10.txt']


def retarget(text):
    text = text.replace('D:/Temp/opencode/r70gate', 'D:/Temp/opencode/r71gate')
    text = text.replace(r'D:\Temp\opencode\r70gate', r'D:\Temp\opencode\r71gate')
    text = text.replace('r70gate', 'r71gate')
    text = text.replace('mirr_m70', 'mirr_m71')
    text = text.replace('build_m70', 'build_m71')
    return text


for ws in ('diag1', 'fix1'):
    target = os.path.join(RT, ws)
    for sub in ('dump', 'specs', 'synth', 'logs'):
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    n = 0
    for f in PY_FILES:
        io.open(os.path.join(target, f), 'w', encoding='utf-8', newline='\n').write(
            retarget(io.open(os.path.join(SRC, f), encoding='utf-8').read()))
        n += 1
    for src, dst in CHAIN.items():
        p = os.path.join(SRC, src)
        if os.path.isfile(p):
            io.open(os.path.join(target, dst), 'w', encoding='utf-8', newline='\n').write(
                retarget(io.open(p, encoding='utf-8').read()))
    for f in TXT_FILES:
        shutil.copyfile(os.path.join(SRC, f), os.path.join(target, f))
    # R70 evidence for reference
    shutil.copyfile(r'F:/Downloads/pythoncdc-main/.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round70/logs/gate/G3v_pycverify_r70.json',
                    os.path.join(target, 'G3v_pycverify_r70.json'))
    print('%s: provisioned (%d instruments)' % (ws, n))
print('filecat.json copied into both workspaces (failure data for the 56 files)')
