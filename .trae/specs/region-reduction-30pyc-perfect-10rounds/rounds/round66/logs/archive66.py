# -*- coding: utf-8 -*-
"""Archive Round 66: six batch workspaces + the center gate chain into the spec round dir.

  python -X utf8 archive66.py

Copies are one-way (scratch -> repo archive). Files above MAXB bytes are skipped so a stray
product dump can't bloat the round record. The repo .gitignore keeps *.pyc out, so only the
.py repro sources land in the commit (the .pyc stay in the working tree for local re-runs).
"""
import io
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')
GATE = r'D:/Temp/opencode/r66gate/center'
SRC6 = r'D:/Temp/opencode/r66gate'
REPO = r'F:/Downloads/pythoncdc-main'
SPEC = os.path.join(REPO, r'.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round66')
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


# 1. the six batch workspaces (FACTS/specs/dump/logs/synth), incl. rejected arms
for n in range(1, 7):
    b = 'diag%d' % n
    src = os.path.join(SRC6, b)
    dst = os.path.join(SPEC, 'batches', b)
    if not os.path.isdir(src):
        continue
    for f in ('FACTS.md', 'ANALYSIS.md', 'BRIEF.md'):
        copy(os.path.join(src, f), os.path.join(dst, f))
    for sub in ('specs', 'dump', 'logs', 'synth', 'quarantine'):
        copytree(os.path.join(src, sub), os.path.join(dst, sub))
    for f in sorted(os.listdir(src)):
        if f.endswith(('.txt', '.py')) and os.path.isfile(os.path.join(src, f)):
            copy(os.path.join(src, f), os.path.join(dst, f))
    for junk in os.listdir(dst):
        if junk.startswith('build_'):
            shutil.rmtree(os.path.join(dst, junk))

# 2. center: gate chain, merged specs, per-arm dumps and lists
copytree(os.path.join(GATE, 'logs'), os.path.join(SPEC, 'logs'))
copytree(os.path.join(GATE, 'dump'), os.path.join(SPEC, 'logs', 'dump'))
copy(os.path.join(GATE, 'CENTER_NOTES.md'), os.path.join(SPEC, 'CENTER_NOTES.md'))
for f in sorted(os.listdir(GATE)):
    p = os.path.join(GATE, f)
    if not os.path.isfile(p):
        continue
    if f.endswith(('.json', '.txt', '.py', '.md')):
        if f.startswith('m66'):
            copy(p, os.path.join(SPEC, 'specs', f))
        else:
            copy(p, os.path.join(SPEC, 'logs', f))
for f in sorted(os.listdir(SRC6)):
    p = os.path.join(SRC6, f)
    if os.path.isfile(p) and f.startswith('m66') and f.endswith('.json'):
        copy(p, os.path.join(SPEC, 'specs', f))

print('archived %d files' % made)
if skipped:
    print('skipped over %d KB: %d' % (MAXB // 1024, len(skipped)))
    for s in skipped:
        print('   ', s)
