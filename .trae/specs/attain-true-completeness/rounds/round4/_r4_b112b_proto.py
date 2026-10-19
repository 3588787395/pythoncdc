#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 B112② prototype: async comp-call in ExpressionReconstructor CALL special-case.

Runtime wrapper (no core edits): before a CALL whose prev significant opcode is
GET_AITER with a ComprehensionObject beneath, wrap stack top into 'Iter' so the
existing sync merge path fires; _parse_comprehension_from_code unwraps Iter and
parse_comprehension_inner re-derives is_async from the comp code object.
"""
import io
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg.ast_generator_v2 import ExpressionReconstructor

_SKIP = ('PRECALL', 'CACHE', 'NOP', 'EXTENDED_ARG', 'RESUME')
_orig = ExpressionReconstructor._process_instruction


def _patched(self, instr):
    prev = getattr(self, '_r4b112_prev_op', None)
    if instr.opname not in _SKIP:
        self._r4b112_prev_op = instr.opname
    if (instr.opname == 'CALL' and (instr.arg or 0) == 0
            and prev == 'GET_AITER'
            and len(self.stack) >= 2
            and self.stack[-2].get('type') == 'ComprehensionObject'
            and self.stack[-1].get('type') != 'Iter'):
        top = self.stack.pop()
        self.stack.append({'type': 'Iter', 'value': top, 'lineno': None})
    return _orig(self, instr)


ExpressionReconstructor._process_instruction = _patched

import pycdc

for pyc, out in ((sys.argv[1], sys.argv[2]),):
    src = pycdc.decompile_pyc(pyc)
    open(out, 'w', encoding='utf-8').write(src)
    print('written', out)
