#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: dump production region set (gen.regions after generate()) for one fn."""
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

print('---- regions (production) ----')
for r in gen.regions:
    bits = ['%s entry=@%s' % (type(r).__name__, r.entry.start_offset)]
    for attr in ('condition_block', 'merge_block', 'true_value_block',
                 'false_value_block', 'header_block', 'back_edge_block'):
        v = getattr(r, attr, None)
        if v is not None:
            bits.append('%s=@%s' % (attr, getattr(v, 'start_offset', v)))
    vt = getattr(r, 'value_target', None)
    mc = getattr(r, 'merge_context', None)
    if vt is not None or mc is not None:
        bits.append('vt=%r ctx=%r' % (vt, mc))
    oc = getattr(r, 'op_chain', None)
    if oc:
        bits.append('op_chain=%s' % [(b.start_offset, o) for b, o in oc])
    ec = getattr(r, 'elif_conditions', None)
    if ec:
        bits.append('elif_conditions=%d' % len(ec))
    if type(r).__name__ == 'IfRegion':
        _ibc = getattr(r, 'inline_boolop_chains', None) or {}
        for _k, _v in _ibc.items():
            if isinstance(_v, dict):
                _ch = _v.get('chain') or _v.get('blocks') or []
                try:
                    _txt = [(getattr(b, 'start_offset', b), o) for b, o in _ch]
                except Exception:
                    _txt = repr(_v)
                bits.append('ibc=%s' % _txt)
            else:
                bits.append('ibc=%r' % (_v,))
        tb = getattr(r, 'then_blocks', None)
        eb = getattr(r, 'else_blocks', None)
        if tb:
            bits.append('then=%s' % sorted(b.start_offset for b in tb))
        if eb:
            bits.append('else=%s' % sorted(b.start_offset for b in eb))
    if type(r).__name__ == 'BoolOpRegion':
        bits.append('is_cond_ctx=%r' % getattr(r, 'is_condition_context', None))
    bb = getattr(r, 'blocks', None)
    if bb:
        bits.append('blocks=%s' % sorted(b.start_offset for b in bb))
    print('  ' + ' '.join(bits))
print('---- generated_blocks ----')
print(sorted(b.start_offset for b in gen.generated_blocks))
