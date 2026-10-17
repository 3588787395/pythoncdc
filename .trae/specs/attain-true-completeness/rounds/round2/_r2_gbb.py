#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace _generate_block_statements_body windows for one function."""
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

_orig = RegionASTGenerator._generate_block_statements_body


def _wrap(self, block, *a, **k):
    _bi = [(i.opname, i.argval) for i in block.instructions] if block is not None else None
    print('[GBB] block=@%s instrs=%s' % (getattr(block, 'start_offset', None), _bi))
    r = _orig(self, block, *a, **k)
    print('[GBB]  -> %s' % json.dumps(r, default=str)[:1200])
    return r


RegionASTGenerator._generate_block_statements_body = _wrap

out = gen.generate()
print('DONE', type(out))
