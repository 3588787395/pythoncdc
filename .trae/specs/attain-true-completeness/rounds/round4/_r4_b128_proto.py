#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 B128 prototype: defer block-level await emission when chain owner is an IfRegion entry.

Runtime wrapper (no core edits): pre-empt _generate_block_statements_body for
blocks containing GET_AWAITABLE whose poll-successor SEND target (owner) is the
entry/condition block of a registered IfRegion.
"""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import region_ast_generator as RAG
from core.cfg.comprehension_generator import is_async_poll_protocol_block
from core.cfg.region_analyzer import IfRegion

_orig = RAG.RegionASTGenerator._generate_block_statements_body


def _patched(self, block, *a, **k):
    if any(i.opname in ('GET_AWAITABLE', 'GET_AITER') for i in block.instructions):
        owner = None
        for succ in (getattr(block, 'successors', None) or []):
            if succ is block:
                continue
            if not is_async_poll_protocol_block(succ.instructions):
                continue
            for i in succ.instructions:
                if i.opname == 'SEND' and i.argval is not None:
                    r = self.cfg.get_block_by_offset(i.argval)
                    if r is not None and r is not succ:
                        owner = r
                    break
            if owner is not None:
                break
        if owner is not None:
            for reg in self.regions:
                if isinstance(reg, IfRegion) and reg.is_block_entry(owner):
                    self.generated_blocks.add(block)
                    return []
    return _orig(self, block, *a, **k)


RAG.RegionASTGenerator._generate_block_statements_body = _patched

import pycdc

pyc = sys.argv[1]
src = pycdc.decompile_pyc(pyc)
open(sys.argv[2], 'w', encoding='utf-8').write(src)
print('written', sys.argv[2])
