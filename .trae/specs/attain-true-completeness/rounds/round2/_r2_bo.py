#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace creation of BoolOpRegion instances. usage: _r2_bo.py <pyc> <name>"""
import io
import marshal
import os
import sys
import traceback
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg import region_analyzer as RA
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

orig_init = RA.BoolOpRegion.__init__


def patched_init(self, *a, **kw):
    orig_init(self, *a, **kw)
    print('BoolOpRegion created entry=@%s merge=@%s op_chain=%s vt=%r cond_ctx=%r' % (
        getattr(self.entry, 'start_offset', None),
        getattr(self.merge_block, 'start_offset', None),
        [(b.start_offset, o) for b, o in (self.op_chain or [])],
        getattr(self, 'value_target', None),
        getattr(self, 'is_condition_context', None)))
    for line in traceback.format_stack()[-6:-1]:
        print('    ' + line.strip().splitlines()[0])


RA.BoolOpRegion.__init__ = patched_init
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.region_analyzer.analyze()
