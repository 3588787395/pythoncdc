# -*- coding: utf-8 -*-
"""R2: dump IfRegion chained-compare fields for one fn."""
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
from core.cfg.region_analyzer import IfRegion, TernaryRegion

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
gen.generate()

for r in gen.regions:
    if isinstance(r, IfRegion):
        print('IfRegion entry=@%s cond=@%s merge=@%s' % (
            getattr(r.entry, 'start_offset', None),
            getattr(r.condition_block, 'start_offset', None),
            getattr(r.merge_block, 'start_offset', None)))
        print('  blocks=%s then=%s else=%s' % (
            [b.start_offset for b in r.blocks],
            [b.start_offset for b in (r.then_blocks or [])],
            [b.start_offset for b in (r.else_blocks or [])]))
        print('  cc_ops=%r cc_blocks=%s cc_left=%r' % (
            getattr(r, 'chained_compare_ops', None),
            [b.start_offset for b in (getattr(r, 'chained_compare_blocks', None) or [])],
            getattr(getattr(r, 'chained_left_instr', None), 'opname', None)))
        print('  cc_left_instrs=%r cc_comp_instrs=%r' % (
            [getattr(i, 'opname', None) for i in (getattr(r, 'chained_comparator_instrs', None) or [])][:8],
            None))
        print('  vt=%r' % (getattr(r, 'value_target', None),))
    elif isinstance(r, TernaryRegion):
        print('TernaryRegion entry=@%s cond=@%s merge=@%s vt=%r' % (
            getattr(r.entry, 'start_offset', None),
            getattr(r.condition_block, 'start_offset', None),
            getattr(r.merge_block, 'start_offset', None),
            getattr(r, 'value_target', None)))
