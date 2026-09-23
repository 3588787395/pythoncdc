# -*- coding: utf-8 -*-
"""Build a mirror core with BOTH R52-A (generator) and R52-B (analyzer) applied.

The two guards live in different files, and this project has already been bitten by a
generator/analyzer pair that measured inert alone yet flipped together, so the shipping
arm must be gated as a pair as well.
"""
import hashlib
import io
import json
import os
import shutil
import sys

REPO = r'F:\Downloads\pythoncdc-main'
ROOT = r'D:/Temp/r52gate'
CR = chr(13)
DST = ROOT + '/mirr_c52ab'
sys.stdout.reconfigure(encoding='utf-8')

if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(DST)
shutil.copytree(os.path.join(REPO, 'core'), os.path.join(DST, 'core'),
                ignore=shutil.ignore_patterns('__pycache__'))
assert not [d for d, _, _ in os.walk(os.path.join(DST, 'core')) if d.endswith('__pycache__')]
shutil.copy(os.path.join(REPO, 'pycdc.py'), os.path.join(DST, 'pycdc.py'))

total_ins = 0
for spec_name in ('spec_r52a.json', 'spec_r52b.json'):
    spec = json.load(io.open(ROOT + '/' + spec_name, encoding='utf-8'))
    rel = spec['file']
    tgt = os.path.join(DST, rel.replace('/', os.sep))
    src_bytes = io.open(os.path.join(REPO, rel.replace('/', os.sep)), 'rb').read()
    assert io.open(tgt, 'rb').read() == src_bytes, 'mirror copy differs from worktree'
    bom = src_bytes[:3] == b'\xef\xbb\xbf'
    txt = src_bytes.decode('utf-8-sig' if bom else 'utf-8')
    nl = '\r\n' if txt.count(CR) else '\n'
    u = txt.replace(nl, '\n')
    edits = spec.get('edits') or [{'anchor': spec['anchor'], 'repl': spec['repl']}]
    patched = u
    for e in edits:
        assert patched.count(e['anchor']) == 1, '%s: anchor %d occurrences' % (spec_name, patched.count(e['anchor']))
        patched = patched.replace(e['anchor'], e['repl'])
    assert patched != u
    ins = sum(e['repl'].count('\n') - e['anchor'].count('\n') for e in edits)
    total_ins += ins
    io.open(tgt, 'w', encoding='utf-8' + ('-sig' if bom else ''), newline='').write(
        patched.replace('\n', nl))
    cb = io.open(tgt, 'rb').read()
    assert cb.count(b'\n') == cb.count(b'\r\n'), 'mixed endings'
    assert (bom == (cb[:3] == b'\xef\xbb\xbf')), 'BOM changed'
    print('%s: %d edits, +%d lines, sha16=%s size=%d'
          % (rel, len(edits), ins, hashlib.sha256(cb).hexdigest()[:16], len(cb)))

import py_compile
for rel in ('core/cfg/region_ast_generator.py', 'core/cfg/region_analyzer.py'):
    py_compile.compile(os.path.join(DST, rel.replace('/', os.sep)), doraise=True, quiet=2)
print('combo mirror %s ready (%d inserted lines total)' % (DST, total_ins))
