# -*- coding: utf-8 -*-
"""Round 39 line A, step 2: print the structural facts available at the elif-chain hoist
decision, without touching core/ (the method is wrapped in-process from outside).

The hoist site is found by source marker instead of by hardcoded name: whichever method of
RegionASTGenerator contains `_elif_shared_merge_tail` is the one we wrap.

usage: python -X utf8 probe39.py <src.py> <func-name> [--core=<mirror-root>]
"""
import functools
import inspect
import io
import os
import py_compile
import sys

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
pos = [x for x in sys.argv[1:] if not x.startswith('--')]
SRC = os.path.abspath(pos[0])
TAIL = pos[1]
ROOT = os.path.abspath(kw.get('core', r'F:\Downloads\pythoncdc-main'))
REPO = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
if ROOT != REPO:
    sys.path.append(REPO)
os.chdir(ROOT)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator as G  # noqa: E402
import pycdc  # noqa: E402

owner = [n for n, f in vars(G).items()
         if callable(f) and getattr(f, '__module__', None) == G.__module__
         and chr(39) + 'type' + chr(39) + ': ' + chr(39) + 'Continue' + chr(39) in
         (inspect.getsource(f) if inspect.isfunction(f) else '')]
NAME = 'MULTI'
LINES = []
COUNT = {}
SRC_OF = {}
ORIGS = {}
for _n in owner:
    SRC_OF[_n] = inspect.getsourcelines(getattr(G, _n))[1]
    ORIGS[_n] = getattr(G, _n)


def _mk(_n, _f):
    def _w(self, *a, **k):
        r = a[0] if a and hasattr(a[0], 'entry') else None
        ent = getattr(getattr(r, 'entry', None), 'start_offset', None)
        key = (_n, ent)
        COUNT[key] = COUNT.get(key, 0) + 1
        out = _f(self, *a, **k)
        LINES.append(({'method': _n, 'def_line': SRC_OF[_n], 'region_entry': ent,
                       'region_type': type(r).__name__,
                       'then': offs(getattr(r, 'then_blocks', None)),
                       'else': offs(getattr(r, 'else_blocks', None)),
                       'merge': getattr(getattr(r, 'merge_block', None), 'start_offset', None),
                       'elif_conds': offs(getattr(r, 'elif_conditions', None)),
                       'elif_bodies': [offs(l) for l in (getattr(r, 'elif_bodies', None) or [])],
                       'elif_final_else': offs(getattr(r, 'elif_final_else', None))}, out))
        return out
    return functools.wraps(_f)(_w)


for _n in owner:
    setattr(G, _n, _mk(_n, ORIGS[_n]))


def wrapped(self, region, *a, **k):
    raise AssertionError('unused')


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


def wrapped(self, region, *a, **k):
    entry = getattr(getattr(region, 'entry', None), 'start_offset', None)
    mb = getattr(region, 'merge_block', None)
    eb0 = (region.elif_bodies or [None])[0] if getattr(region, 'elif_bodies', None) else None
    last = eb0[-1] if eb0 else None
    rec = {'entry': entry,
           'then': offs(getattr(region, 'then_blocks', None)),
           'else': offs(getattr(region, 'else_blocks', None)),
           'elif_conds': offs(getattr(region, 'elif_conditions', None)),
           'elif_bodies': [offs(l) for l in (region.elif_bodies or [])],
           'elif_final_else': offs(getattr(region, 'elif_final_else', None)),
           'merge_block': getattr(mb, 'start_offset', None),
           'elif_bodies[0][-1] is merge_block': (last is not None and last is mb),
           'current_loop_entry': getattr(getattr(self, '_current_loop', None), 'entry', None)
           and self._current_loop.entry.start_offset,
           'succ_of_elif_last': sorted(offs(getattr(last, 'successors', None)) or [])}
    out = ORIG(self, region, *a, **k)
    LINES.append((rec, out))
    return out


# (wrapping already applied per-method above)

work = os.path.join(HERE, 'probe39_work')
os.makedirs(work, exist_ok=True)
orig_pyc = os.path.join(work, 'orig.pyc')
py_compile.compile(SRC, cfile=orig_pyc, doraise=True, quiet=2)
prod = pycdc.decompile_pyc(orig_pyc)

import dis  # noqa: E402
import types  # noqa: E402
with open(orig_pyc, 'rb') as f:
    f.read(16)
    top = marshal_loads = types.CodeType and __import__('marshal').load(f)
names = set()


def walk(c):
    if c.co_name.endswith(TAIL):
        names.update(getattr(b, 'start_offset', -1) for b in [])
        print('=== target %s offsets in code: FOR_ITER/JUMP ===' % c.co_name)
        for i in dis.get_instructions(c):
            if 'JUMP' in i.opname or i.opname in ('FOR_ITER', 'STORE_SUBSCR'):
                print('   @%-4d %-26s -> %s' % (i.offset, i.opname,
                                                i.argval if isinstance(i.argval, int) else ''))
    for x in c.co_consts:
        if isinstance(x, types.CodeType):
            walk(x)


walk(top)
from pprint import pformat as _pf  # noqa: E402
print('=== %d Continue-constructing methods wrapped; %d calls ===' % (len(owner), len(LINES)))
for _k, _v in sorted(COUNT.items()):
    print('   %dx  %s (def line %s) region_entry=%s' % (_v, _k[0], SRC_OF[_k[0]], _k[1]))
print('--- per-call detail (only those whose emission contains a Continue) ---')
for rec, out in LINES:
    txt = _pf(out, width=200)
    if 'Continue' not in txt:
        continue
    print(_pf(rec, width=110))
    print('   -> emitted:', txt[:600].replace('\n', ' | '))
    print()
print('=== product ===')
print(prod)
