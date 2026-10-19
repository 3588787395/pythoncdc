#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 synth b112a trace v3: dispatcher-level + generated_blocks inspection."""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG

_instances = []
_orig_init = RAG.RegionASTGenerator.__init__


def _init(self, *a, **k):
    _orig_init(self, *a, **k)
    _instances.append(self)


RAG.RegionASTGenerator.__init__ = _init

_dispatch = RAG.RegionASTGenerator._generate_block_statements


def dispatch(self, block, *a, **k):
    r = _dispatch(self, block, *a, **k)
    _cn = getattr(getattr(self.cfg, 'code', None), 'co_name', '?')
    print(f'[DISP] fn={_cn} @{block.start_offset} -> {len(r) if r else r}')
    return r


RAG.RegionASTGenerator._generate_block_statements = dispatch

import pycdc

src = pycdc.decompile_pyc(r'test_repros/round4/rec1_synth_b112a_asyncgen.pyc')
open(sys.argv[1], 'w', encoding='utf-8').write(src)

for inst in _instances:
    code = getattr(inst.cfg, 'code', None)
    if getattr(code, 'co_name', None) == 's_plain':
        print('--- s_plain generator state ---')
        print('generated block offsets:', sorted(
            b.start_offset for b in inst.generated_blocks))
        for key, b in sorted(inst.cfg.blocks.items()):
            print(f'  block @{b.start_offset} generated={b in inst.generated_blocks}')
print('written', sys.argv[1])
