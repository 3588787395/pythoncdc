# -*- coding: utf-8 -*-
"""Trace which lines of _generate_block_statements_body run for one block."""
import json
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.cfg_builder import CFGBuilder  # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]
off = int(sys.argv[3])

raw = open(pyc, 'rb').read()
code = marshal.loads(raw[16:])
target = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == fname:
        target = c
        break
cfg = CFGBuilder().build(target)
an = RegionAnalyzer(cfg)
an.analyze()
gen = RegionASTGenerator(cfg)
blk = cfg.get_block_by_offset(off)

target_file = os.path.abspath('core/cfg/region_ast_generator.py').lower()
hits = []


def tracer(frame, event, arg):
    if event == 'line' and frame.f_code.co_filename.lower() == target_file:
        if 61621 <= frame.f_lineno <= 66049:
            hits.append(frame.f_lineno)
    return tracer


sys.settrace(tracer)
try:
    res = gen._generate_block_statements_body(blk)
finally:
    sys.settrace(None)

print('result:', json.dumps(res, ensure_ascii=False, default=repr)[:400])
print('line hits (in order):')
print(hits)
