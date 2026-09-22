# -*- coding: utf-8 -*-
"""Round 39 line A, step 6: where did the arm-tail back-edge block go?

Wraps RegionASTGenerator._generate_region (and a few emitters) from outside and,
for the target CFG, records for each call:
    region type/entry, blocks newly consumed by that call, statement shape returned
so we can see whether the elif-arm tail (@58) and the loop-tail back edge (@60)
are consumed INSIDE the if region or at loop level, and which one produces the
single emitted `continue`.

usage: python -X utf8 probe_trace.py <src.py> <func-name> [--core=<mirror-root>]
"""
import functools
import importlib.util
import io
import json
import os
import py_compile
import sys

kw = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
pos = [x for x in sys.argv[1:] if not x.startswith('--')]
SRC = os.path.abspath(pos[0]) if pos else None
TAIL = pos[1] if len(pos) > 1 else ''
REPO = r'F:\Downloads\pythoncdc-main'
ROOT = os.path.abspath(kw.get('core', REPO))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
if ROOT != REPO:
    sys.path.append(REPO)
os.chdir(ROOT)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg.region_ast_generator import RegionASTGenerator as G  # noqa: E402
from core.cfg.region_analyzer import IfRegion, LoopRegion, TryExceptRegion  # noqa: E402

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

EVENTS = []
TARGET = {'hit': False}


def offs(bs):
    return sorted(getattr(b, 'start_offset', None) for b in (bs or []) if b is not None)


def desc(r):
    if r is None:
        return 'NONE'
    return '%s@%s' % (type(r).__name__,
                      getattr(getattr(r, 'entry', None), 'start_offset', None))


def shape(stmts, depth=0):
    """Compact statement-tree rendering, marking Continue nodes."""
    out = []
    for s in stmts or []:
        if not isinstance(s, dict):
            out.append(repr(s))
            continue
        t = s.get('type')
        extra = ''
        if t == 'If':
            extra = '(then=%s orelse=%s)' % (shape(s.get('body'), depth + 1),
                                             shape(s.get('orelse'), depth + 1))
        elif t in ('For', 'While'):
            extra = '(body=%s orelse=%s)' % (shape(s.get('body'), depth + 1),
                                             shape(s.get('orelse'), depth + 1))
        elif t in ('TryExcept', 'Try'):
            extra = '(body=%s handlers=%s)' % (
                shape(s.get('body'), depth + 1),
                [shape(h.get('body'), depth + 1) if isinstance(h, dict) else h
                 for h in (s.get('handlers') or [])])
        out.append('%s%s' % (t, extra))
    return '[' + ' '.join(out) + ']'


def make(tag, M):
    @functools.wraps(M)
    def wrapped(self, *a, **k):
        cfgname = getattr(getattr(self, 'cfg', None), 'name', '?')
        if not TARGET['hit'] or (TAIL and TAIL not in cfgname):
            return M(self, *a, **k)
        before = set(getattr(self, 'generated_offsets', set()))
        beforeb = set(getattr(self, 'generated_blocks', set()))
        res = M(self, *a, **k)
        added = sorted(set(getattr(self, 'generated_offsets', set())) - before)
        addedb = [getattr(b, 'start_offset', None) for b in
                  set(getattr(self, 'generated_blocks', set())) - beforeb]
        rec = {'tag': tag, 'args': [desc(x) if hasattr(x, 'blocks') or hasattr(x, 'entry')
                                    else (offs(x) if isinstance(x, (list, tuple, set)) and x and
                                          hasattr(x[0], 'start_offset') else None)
                                    for x in a[:3]],
               'consumed_offsets': added,
               'consumed_blocks': sorted(x for x in addedb if x is not None),
               'result': shape(res) if isinstance(res, list) else type(res).__name__}
        EVENTS.append(rec)
        return res
    return wrapped


SITES = {}
for nm in ('_generate_region', '_generate_degraded_statements', '_process_if_blocks',
           '_loop_generate_body', '_if_generate_normal', '_if_generate_then_branch'):
    M = getattr(G, nm, None)
    if M is not None:
        SITES[nm] = M
        setattr(G, nm, make(nm, M))

GEN = G.generate


@functools.wraps(GEN)
def gen(self, *a, **k):
    cfgname = getattr(getattr(self, 'cfg', None), 'name', '?')
    if TAIL and TAIL not in cfgname:
        return GEN(self, *a, **k)
    TARGET['hit'] = True
    EVENTS.clear()
    r = GEN(self, *a, **k)
    TARGET['hit'] = False
    print('\n### generate(%s) final consumed offsets: %s'
          % (cfgname, sorted(getattr(self, 'generated_offsets', set()))))
    print('### result shape: %s' % shape(r))
    for e in EVENTS:
        print(json.dumps(e, ensure_ascii=False))
    return r


G.generate = gen

PYC = SRC if SRC.lower().endswith('.pyc') else os.path.join(HERE, 'probe_trace.pyc')
if PYC is not SRC:
    py_compile.compile(SRC, cfile=PYC, doraise=True, quiet=2)
import pycdc  # noqa: E402
prod = pycdc.decompile_pyc(PYC)
PRODPY = os.path.join(HERE, 'probe_trace_prod.py')
io.open(PRODPY, 'w', encoding='utf-8').write(prod)
print('================ PRODUCT ================')
print(prod)
o_map = r10._load_map(PYC)
d_map = r10._compile_map(PRODPY)
for key in o_map:
    if key in d_map:
        print('strict %-24s %s' % (key, r10.strict_compare(o_map[key], d_map[key])))
