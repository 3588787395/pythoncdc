#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 trace4: 追踪 _generate_if / _generate_boolop / _generate_ternary 的生成与抢占。"""
import io
import json
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])
targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)


def wrap(method_name, label):
    orig = getattr(gen, method_name)

    def traced(region, *a, **k):
        ent = getattr(region, 'entry', None)
        ent = ent and ent.start_offset
        mg = getattr(region, 'merge_block', None)
        mg = mg and mg.start_offset
        cond = getattr(region, 'condition_block', None)
        cond = cond and cond.start_offset
        print('[enter %s entry=@%s cond=@%s merge=@%s ctx=%s vt=%s]' % (
            label, ent, cond, mg,
            getattr(region, 'merge_context', None),
            getattr(region, 'value_target', None)))
        out = orig(region, *a, **k)
        s = json.dumps(out, default=str) if out is not None else 'None'
        print('[exit %s entry=@%s] received_blocks=%s -> %s' % (
            label, ent,
            [b.start_offset for b in (getattr(region, 'blocks', None) or [])][:12],
            s[:700]))
        return out

    setattr(gen, method_name, traced)


wrap('_generate_if', 'IF')
wrap('_generate_boolop_impl', 'BOOLOP')
wrap('_generate_ternary', 'TERN')

try:
    ast = gen.generate()
    print('---- final AST (compact) ----')
    print(json.dumps(ast, default=str)[:4000])
except Exception:
    import traceback
    traceback.print_exc()
