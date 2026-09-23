# -*- coding: utf-8 -*-
"""Enumerate code objects the comprehension-ternary patch can possibly reach.

The patch lives inside ComprehensionGenerator._detect_comp_ternary and only fires
when the FALSE region of a comprehension element contains a forward conditional
jump (i.e. a second nested conditional). So the exhaustive set of code objects
whose emitted text can change is: comprehension code objects with >=2 forward
conditional jumps. No decompilation involved: marshal-load each pyc and dis the
comprehension code objects.

usage: python -X utf8 reach54.py
"""
import dis
import glob
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')
_s = importlib.util.spec_from_file_location('ml54', REPO + '/scripts/_marshal_helper.py')
ml = None
if os.path.exists(_s.origin):
    ml = importlib.util.module_from_spec(_s)
    _s.loader.exec_module(ml)
import marshal

FWD = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
       'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
       'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')


def load(p):
    b = io.open(p, 'rb').read()
    return marshal.loads(b[16 if len(b) > 16 and b[:4] != b'\x00\x00\x00\x00' else 16:])


def walk(co, out, depth=0):
    nm = co.co_name
    if nm in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>'):
        n = 0
        for ins in dis.get_instructions(co):
            if ins.opname in FWD:
                n += 1
        out.append((nm, n))
    for k in co.co_consts:
        if hasattr(k, 'co_code'):
            walk(k, out, depth + 1)


files = sorted(glob.glob(REPO + '/site-packages/**/*.pyc', recursive=True))
hits = []
total_comps = 0
for p in files:
    try:
        co = load(p)
    except Exception as e:
        continue
    out = []
    walk(co, out)
    for nm, n in out:
        total_comps += 1
        if n >= 2:
            hits.append((p.replace(REPO + '/site-packages/', '').replace('\\', '/'), n))
print('pyc files=%d comprehension code objects=%d with >=2 forward cond jumps=%d'
      % (len(files), total_comps, len(hits)))
for h, n in sorted(hits, key=lambda x: -x[1])[:25]:
    print('   %2d  %s' % (n, h[:96]))
io.open(r'D:/Temp/r54gate/reach54.txt', 'w', encoding='utf-8', newline='').write(
    '\n'.join(REPO.replace('\\', '/') + '/site-packages/' + h.replace('/', os.sep) for h, n in hits) + '\n')
