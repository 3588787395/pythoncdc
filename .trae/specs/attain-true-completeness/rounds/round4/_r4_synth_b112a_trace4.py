#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 synth b112a trace v4: who marks landing @56 generated (stack trace)."""
import io
import os
import sys
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG


class TracingSet(set):
    def __init__(self, owner):
        super().__init__()
        self._owner = owner

    def add(self, item):
        try:
            code = getattr(getattr(self._owner.cfg, 'code', None), 'co_name', '?')
        except Exception:
            code = '?'
        if code == 's_plain' and hasattr(item, 'start_offset') and item.start_offset in (22, 48, 56):
            stack = traceback.extract_stack()[-6:-1]
            print(f'[ADD] @{item.start_offset} by:')
            for fr in stack:
                print(f'      {fr.name} {os.path.basename(fr.filename)}:{fr.lineno}')
        super().add(item)


_orig_init = RAG.RegionASTGenerator.__init__


def _init(self, *a, **k):
    _orig_init(self, *a, **k)
    self.generated_blocks = TracingSet(self)


RAG.RegionASTGenerator.__init__ = _init

import pycdc

src = pycdc.decompile_pyc(r'test_repros/round4/rec1_synth_b112a_asyncgen.pyc')
open(sys.argv[1], 'w', encoding='utf-8').write(src)
print('written', sys.argv[1])
