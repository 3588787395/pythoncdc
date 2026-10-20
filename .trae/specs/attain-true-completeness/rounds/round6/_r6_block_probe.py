# -*- coding: utf-8 -*-
"""R6 probe: call _generate_block_statements on a block and dump result."""
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
print('block', off, [i.opname for i in blk.instructions])
print(json.dumps(gen._generate_block_statements(blk), indent=1, ensure_ascii=False, default=repr))
