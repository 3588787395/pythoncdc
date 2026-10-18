#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace region dispatch for one function — log which regions get
generated and what they return (types), to find who swallows the and-tail."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

pyc = sys.argv[1]
name = sys.argv[2]

data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)


def _entry_off(r):
    e = getattr(r, 'entry', None)
    return getattr(e, 'start_offset', None) if e is not None else None


def wrap(meth_name):
    orig = getattr(gen, meth_name)

    def w(region, *a, **k):
        r = orig(region, *a, **k)
        try:
            desc = ''
            if r is not None:
                if isinstance(r, list):
                    desc = '[' + ','.join((i.get('type') if isinstance(i, dict) else type(i).__name__)
                                          for i in r) + ']'
                else:
                    desc = type(r).__name__
            extra = ''
            for attr in ('chained_compare_ops', 'is_cond_ctx', 'op_chain'):
                v = getattr(region, attr, None)
                if v:
                    extra += ' %s=%r' % (attr, v)
            sys.stdout.write('%s entry=@%s -> %s%s\n'
                             % (meth_name, _entry_off(region), desc or 'None', extra))
        except Exception:
            pass
        return r
    return w


for m in ('_generate_if', '_generate_boolop', '_generate_loop', '_generate_try',
          '_generate_ternary', '_generate_region'):
    try:
        setattr(gen, m, wrap(m))
    except Exception:
        pass

res = gen.generate()
import json
sys.stdout.write('---- module body:\n')
sys.stdout.write(json.dumps(res, ensure_ascii=False, default=str)[:1500])
