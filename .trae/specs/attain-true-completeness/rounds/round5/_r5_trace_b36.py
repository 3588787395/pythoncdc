#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pycdc
from core.cfg.region_ast_generator import RegionASTGenerator

TARGET = sys.argv[2]
_o = RegionASTGenerator._b36_cross_block_return_value


def patched(self, block):
    r = _o(self, block)
    try:
        target = TARGET in (self.cfg.code.co_qualname or '')
    except Exception:
        target = False
    if target:
        def st(off):
            b = self.cfg.get_block_by_offset(off)
            return 'gen=%s owner=%s' % (
                b in self.generated_blocks,
                type(self.region_analyzer.block_to_region.get(b)).__name__)
        print('B36 @%s -> %s' % (block.start_offset, r))
        for p in block.predecessors:
            print('  pred @%s %s' % (p.start_offset, st(p.start_offset)))
        print('  b110 %s' % st(110))
    return r


RegionASTGenerator._b36_cross_block_return_value = patched
src = pycdc.decompile_pyc(sys.argv[1])
for i, line in enumerate(src.splitlines(), 1):
    print('%3d %s' % (i, line))
