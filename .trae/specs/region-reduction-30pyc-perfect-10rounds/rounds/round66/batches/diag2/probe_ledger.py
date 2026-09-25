# -*- coding: utf-8 -*-
"""diag2 R66 probe #3: statement-emission ledger on the LANDED core (read-only).

Wraps a chosen set of generator methods and prints, for every returned statement
that mentions --mark, a compact rendering + the region identity + the emitting
call stack. Also reports per-region call counts and duplicate AST ids.

usage: python -X utf8 probe_ledger.py <pyc> --mark=STR [--wrap=a,b] [--out=file]
"""
import argparse
import io
import json
import sys
import traceback

REPO = r'F:\Downloads\pythoncdc-main'
sys.dont_write_bytecode = True
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

ap = argparse.ArgumentParser()
ap.add_argument('pyc')
ap.add_argument('--mark', default='')
ap.add_argument('--wrap', default='_generate_ternary')
ap.add_argument('--out', default='')
a = ap.parse_args()

import pycdc  # noqa
import core.cfg.region_ast_generator as G  # noqa

log = []
seen_ids = {}


def render(node):
    return repr(node)[:520]


def mentions(node):
    return (not a.mark) or a.mark in repr(node)


def stack_tail(limit=12):
    fr = traceback.extract_stack()[:-2]
    keep = [f for f in fr if 'region_ast_generator' in f.filename]
    return ' <- '.join('%s:%d' % (f.name, f.lineno) for f in keep[-limit:])


def bdesc(b):
    if b is None:
        return None
    try:
        return '%d(%dins,%s)' % (b.start, len(b.instructions),
                                 b.instructions[-1].opname)
    except Exception:
        return '?'


def rdesc(r):
    return '%s cond=%s merge=%s ctx=%s vt=%s blocks=%s' % (
        type(r).__name__, bdesc(getattr(r, 'condition_block', None)),
        bdesc(getattr(r, 'merge_block', None)),
        getattr(r, 'merge_context', None), getattr(r, 'value_target', None),
        [bdesc(b) for b in (getattr(r, 'blocks', None) or [])])


def wrap(name):
    orig = getattr(G.RegionASTGenerator, name)

    def wrapper(self, *args, **kw):
        r = orig(self, *args, **kw)
        try:
            stmts = r if isinstance(r, list) else ([r] if isinstance(r, dict) else [])
            region = args[0] if args and hasattr(args[0], 'blocks') else None
            for s in stmts:
                if mentions(s):
                    sid = id(s)
                    prev = seen_ids.get(sid)
                    log.append('%s ret: %s%s\n   region=%s\n   stack=%s'
                               % (name, render(s),
                                  '' if prev is None else '  ***SAME-DICT-AS-#%d***' % prev,
                                  rdesc(region) if region else '-', stack_tail()))
                    seen_ids[sid] = len(log) - 1
        except Exception as e:
            log.append('wrap-error %s %r' % (name, e))
        return r
    wrapper.__name__ = name
    setattr(G.RegionASTGenerator, name, wrapper)


for nm in a.wrap.split(','):
    wrap(nm.strip())

text = pycdc.decompile_pyc(a.pyc)
out = a.out or 'logs/ledger.txt'
with io.open(out, 'w', encoding='utf-8') as fh:
    fh.write('=== %s mark=%s  entries=%d\n' % (a.pyc, a.mark, len(log)))
    for i, l in enumerate(log):
        fh.write('[%d]\n%s\n' % (i, l))
    fh.write('\n=== product lines with mark ===\n')
    for n, line in enumerate(text.split('\n'), 1):
        if a.mark and a.mark in line:
            fh.write('%d| %s\n' % (n, line))
    fh.write('\n=== duplicate AST dict ids: %d of %d ===\n'
             % (len(log) - len(seen_ids), len(log)))
print(io.open(out, encoding='utf-8').read()[:24000])
