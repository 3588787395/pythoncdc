# -*- coding: utf-8 -*-
"""R6 trace: who consumes the match case-body blocks in a handler host."""
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]
watch = set(int(x) for x in (sys.argv[3].split(',') if len(sys.argv) > 3 and sys.argv[3] else []))

with open(pyc, 'rb') as f:
    code = marshal.loads(f.read()[16:])

target = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == fname:
        target = c
        break

cfg = build_cfg(target)
gen = RegionASTGenerator(cfg)

_orig_hbs = RegionASTGenerator._generate_handler_body_statements
_orig_match = RegionASTGenerator._generate_match


def traced_hbs(self, block):
    off = block.start_offset
    res = _orig_hbs(self, block)
    if not watch or off in watch:
        print('[hbs] blk@%s -> %s' % (off, res))
    return res


def traced_match(self, region):
    print('[match] entry=%s cases=%s' % (
        region.entry.start_offset if region.entry else None,
        [[b.start_offset for b in body] for body in (region.case_bodies or [])]))
    for body in (region.case_bodies or []):
        for b in body:
            print('   blk@%s already_generated=%s role=%s' % (
                b.start_offset,
                b in self.generated_blocks,
                self.region_analyzer.get_block_role(b)))
    res = _orig_match(self, region)
    if res:
        for c in res.get('cases', []):
            body = c.get('body')
            print('   case body=%s' % body)
    return res


RegionASTGenerator._generate_handler_body_statements = traced_hbs
RegionASTGenerator._generate_match = traced_match

out = gen.generate()
print('generated ok')
