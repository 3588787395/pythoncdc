#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: raw instruction dump per CFG block for named functions."""
import dis
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

pyc = sys.argv[1]
names = sys.argv[2:]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


for name in names:
    targets = []
    find_code(code, name, targets)
    if not targets:
        print('== %s NOT FOUND' % name)
        continue
    co = targets[-1]
    cfg = build_cfg(co)
    print('==== %s ====' % name)
    for _bk in cfg.blocks:
        b = cfg.blocks[_bk] if isinstance(cfg.blocks, dict) else _bk
        print('-- block @%d --' % b.start_offset)
        for ins in b.instructions:
            arg = '' if getattr(ins, 'arg', None) is None else ' %r' % (ins.arg,)
            tgt = ''
            if ins.opname.startswith(('JUMP', 'FOR_ITER', 'SEND', 'POP_JUMP', 'SETUP')):
                t = getattr(ins, 'target', None)
                if t is None:
                    t = getattr(ins, 'jump_target', None)
                if t is None:
                    t = getattr(ins, 'argval', None)
                tgt = ' -> @%s' % (getattr(t, 'start_offset', t),)
            print('   @%-4d %-28s%s%s' % (ins.offset, ins.opname, arg, tgt))
