#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: dump generated AST/source for one function (generate-only harness)."""
import ast
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
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
out = gen.generate()
print('TYPE', type(out))
if isinstance(out, dict):
    for k, v in out.items():
        if isinstance(v, ast.AST):
            print('== %s ==' % k)
            try:
                print(ast.unparse(v))
            except Exception:
                print(ast.dump(v))
        elif isinstance(v, list):
            print('== %s == %d items' % (k, len(v)))
            for item in v:
                if isinstance(item, ast.AST):
                    try:
                        print(ast.unparse(item))
                    except Exception:
                        print(ast.dump(item))
                else:
                    print(repr(item)[:800])
        else:
            print('== %s ==' % k, repr(v)[:800])
    _dump = out.get('_dump') or out
    try:
        for _k, _v in (out.get('toplevel_code') or {}).items() if isinstance(out.get('toplevel_code'), dict) else []:
            print('== toplevel %s ==' % _k)
    except Exception:
        pass
else:
    if isinstance(out, ast.AST):
        try:
            print(ast.unparse(out))
        except Exception:
            print(ast.dump(out))
    else:
        print(repr(out)[:4000])
print('==== FULL JSON ====')
print(json.dumps(out, indent=1, default=str))
