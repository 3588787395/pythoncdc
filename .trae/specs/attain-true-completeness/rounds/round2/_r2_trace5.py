#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 trace5: 追踪块级派发（_generate_region / _process_if_blocks / _generate_ternary）。"""
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


def wrap(method_name, label, fmt):
    orig = getattr(gen, method_name)

    def traced(*a, **k):
        print('[%s] %s' % (label, fmt(a, k)))
        out = orig(*a, **k)
        if out is None:
            print('[%s] -> None' % label)
        return out

    setattr(gen, method_name, traced)


wrap('_generate_region', 'REG', lambda a, k: 'block=@%s' % getattr(a[0], 'start_offset', a[0]))
wrap('_generate_ternary', 'TERN', lambda a, k: 'region entry=@%s' % getattr(getattr(a[0], 'entry', None), 'start_offset', '?'))
wrap('_if_generate_normal', 'IFNORM', lambda a, k: 'region entry=@%s' % getattr(getattr(a[0], 'entry', None), 'start_offset', '?'))
if hasattr(gen, '_process_if_blocks'):
    wrap('_process_if_blocks', 'PIB', lambda a, k: 'blocks=%s' % [getattr(b, 'start_offset', b) for b in (a[0] or [])][:20])

try:
    ast = gen.generate()
    print('---- final AST (compact) ----')
    print(json.dumps(ast, default=str)[:4000])
except Exception:
    import traceback
    traceback.print_exc()
