#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: dump IfRegion field detail (cond/then/else/merge instrs) for one fn."""
import io
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
from core.cfg.region_analyzer import IfRegion

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
regs = gen.region_analyzer.analyze()


def bins(b):
    if b is None:
        return 'None'
    return '[%s]' % ', '.join(
        '%s%s' % (i.opname, '' if i.arg is None else '(%s)' % (i.arg,))
        for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))


for r in regs:
    if isinstance(r, IfRegion):
        print('IfRegion entry=@%s cond=@%s' % (
            getattr(r.entry, 'start_offset', None),
            getattr(getattr(r, 'condition_block', None), 'start_offset', None)))
        print('  cond : %s' % bins(getattr(r, 'condition_block', None)))
        print('  then : %s' % ([getattr(b, 'start_offset', None) for b in (getattr(r, 'then_blocks', None) or [])],))
        print('  else : %s' % ([getattr(b, 'start_offset', None) for b in (getattr(r, 'else_blocks', None) or [])],))
        print('  merge: @%s %s' % (getattr(getattr(r, 'merge_block', None), 'start_offset', None),
                                   bins(getattr(r, 'merge_block', None))))
        print('  cond jt last: %s' % (
            getattr(getattr(getattr(r, 'condition_block', None), 'get_last_instruction', lambda: None)(), 'opname', None),))
