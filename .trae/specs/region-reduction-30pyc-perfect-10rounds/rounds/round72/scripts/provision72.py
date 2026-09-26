# -*- coding: utf-8 -*-
"""Round 72 step 0: provision the r72gate workspaces (diag1 read-only diagnosis,
fix1 = comprehension/genexpr family, fix2 = head control-flow family) from the proven
r71gate centre instruments, retargeting only workspace-root string literals
(r71gate -> r72gate).  Nothing is executed; no repository file is touched."""
import io
import os
import shutil
import sys

SRC = r'D:/Temp/opencode/r71gate/center'
RT = r'D:/Temp/opencode/r72gate'
sys.stdout.reconfigure(encoding='utf-8')

PY_FILES = ['h62.py', 'align.py', 'regdump.py', 'disf.py', 'nhunks.py', 'cstrict.py',
            'cstrict67.py', 'sstrict67.py', 'strict_repo67.py', 'closeout69.py',
            'battable67.py', 'dumpfn.py', 'mk_spec.py', 'probe_chain.py', 'blast67.py',
            'audit5_g5_67.py', 'nested_diff.py', 'gates71a.py', 'gates71a_fix.py',
            'gates71b.py', 'mkblast71.py', 'merge_g3v71.py']
CHAIN = {'mbuild71.py': 'mbuild72.py', 'mkfinal71.py': 'mkfinal72.py',
         'land71.py': 'land72.py', 'mkmirr_prev71.py': 'mkmirr_prev72.py',
         'mkarchive71r.py': 'mkarchive72r.py'}
TXT_FILES = ['battery.txt', 'canary.txt', 'shapes_r63.txt', 'all402.txt', 'all16.txt',
             'targets10.txt', 'all56.txt', 'div48.txt', 'nine.txt']


def retarget(text):
    text = text.replace('D:/Temp/opencode/r71gate', 'D:/Temp/opencode/r72gate')
    text = text.replace(r'D:\Temp\opencode\r71gate', r'D:\Temp\opencode\r72gate')
    text = text.replace('r71gate', 'r72gate')
    text = text.replace('mirr_m71', 'mirr_m72')
    text = text.replace('build_m71', 'build_m72')
    text = text.replace('round 71', 'round 72')
    text = text.replace('Round 71', 'Round 72')
    text = text.replace('_r71', '_r72')
    text = text.replace('r71_', 'r72_')
    return text


for ws in ('diag1', 'fix1', 'fix2', 'center'):
    target = os.path.join(RT, ws)
    for sub in ('dump', 'specs', 'synth', 'logs'):
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    n = 0
    for f in PY_FILES:
        p = os.path.join(SRC, f)
        if not os.path.isfile(p):
            continue
        io.open(os.path.join(target, f), 'w', encoding='utf-8', newline='\n').write(
            retarget(io.open(p, encoding='utf-8').read()))
        n += 1
    for src, dst in CHAIN.items():
        p = os.path.join(SRC, src)
        if os.path.isfile(p):
            io.open(os.path.join(target, dst), 'w', encoding='utf-8', newline='\n').write(
                retarget(io.open(p, encoding='utf-8').read()))
    for f in TXT_FILES:
        p = os.path.join(SRC, f)
        if os.path.isfile(p):
            shutil.copyfile(p, os.path.join(target, f))
    # R71 evidence for reference
    shutil.copyfile(r'D:/Temp/opencode/r71gate/center/logs/G3v_pycverify_r71.json',
                    os.path.join(target, 'G3v_pycverify_r71.json'))
    print('%s: provisioned (%d instruments)' % (ws, n))
print('workspaces ready under', RT)
