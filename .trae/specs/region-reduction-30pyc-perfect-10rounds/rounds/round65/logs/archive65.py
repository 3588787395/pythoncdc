# -*- coding: utf-8 -*-
"""Archive Round 65: six batch workspaces + the center gate chain into the spec round dir,
and the synthetic repros into test_repros/round65_diagN/.

  python -X utf8 archive65.py

Copies are one-way (scratch -> repo archive). Files above MAXB bytes are skipped so a stray
product dump can't bloat the round record; *.pyc repros are copied for local re-runs but the
repo .gitignore keeps them out of the commit (only .py is archived per convention).
"""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
GATE = r'D:/Temp/opencode/r65gate'
REPO = r'F:/Downloads/pythoncdc-main'
SPEC = os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round65')
MAXB = 400 * 1024
made = 0
skipped = []


def copy(src, dst):
    global made
    if not os.path.isfile(src):
        return
    if os.path.getsize(src) > MAXB:
        skipped.append(src.replace('\\', '/'))
        return
    d = os.path.dirname(dst)
    if not os.path.isdir(d):
        os.makedirs(d)
    shutil.copy2(src, dst)
    made += 1


def copytree(src, dst, keep=lambda p: True):
    if not os.path.isdir(src):
        return
    for root, dirs, files in os.walk(src):
        dirs[:] = [x for x in dirs if x != '__pycache__']
        for f in files:
            p = os.path.join(root, f)
            if not keep(p):
                continue
            copy(p, os.path.join(dst, os.path.relpath(p, src).replace('\\', '/')))


for d in range(6):
    b = 'diag%d' % d
    src = os.path.join(GATE, b)
    dst = os.path.join(SPEC, 'batches', b)
    if not os.path.isdir(src):
        continue
    for f in ('FACTS.md', 'ANALYSIS.md', 'BRIEF.md'):
        copy(os.path.join(src, f), os.path.join(dst, f))
    copytree(os.path.join(src, 'specs'), os.path.join(dst, 'specs'))
    copytree(os.path.join(src, 'dump'), os.path.join(dst, 'dump'))
    copytree(os.path.join(src, 'logs'), os.path.join(dst, 'logs'))
    copytree(os.path.join(src, 'synth'), os.path.join(dst, 'synth'))
    for f in sorted(os.listdir(src)):
        if f.endswith(('.txt', '.py')) and os.path.isfile(os.path.join(src, f)):
            copy(os.path.join(src, f), os.path.join(dst, f))
    # generated decompiler products are NOT archive material
    for junk in ('build_landed', 'build_head'):
        j = os.path.join(dst, junk)
        if os.path.isdir(j):
            shutil.rmtree(j)

# center: gate logs, dumps, lists, tooling
copytree(os.path.join(GATE, 'logs'), os.path.join(SPEC, 'logs'))
copytree(os.path.join(GATE, 'dump'), os.path.join(SPEC, 'logs'))
for f in sorted(os.listdir(GATE)):
    p = os.path.join(GATE, f)
    if not os.path.isfile(p):
        continue
    if f.endswith(('.json', '.txt', '.py', '.md')):
        if f.startswith('m65_'):
            copy(p, os.path.join(SPEC, 'specs', f))
        else:
            copy(p, os.path.join(SPEC, 'logs', f))

# synthetic repros -> test_repros (battery material)
for d, names in ((1, ('r65_trytail.py', 'r65_trytail.pyc', 'r65_trytail_w.py', 'r65_trytail_w.pyc')),
                 (2, ('fs2.py', 'fs2.pyc', 'fsrepro.py', 'fsrepro.pyc')),
                 (5, ('r65d5_probe.py', 'r65d5_probe.pyc'))):
    dst = os.path.join(REPO, 'test_repros', 'round65_diag%d' % d)
    for n in names:
        copy(os.path.join(GATE, 'diag%d' % d, 'synth', n), os.path.join(dst, n))

print('archived %d files' % made)
if skipped:
    print('skipped oversize (>%d KB): %d' % (MAXB // 1024, len(skipped)))
    for s in skipped[:10]:
        print('   ', s)
