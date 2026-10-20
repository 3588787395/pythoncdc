# -*- coding: utf-8 -*-
"""R5 v2 结构追踪：dump _collect_nested_literal_match 收集结果。

用法: python -X utf8 _r5_v2_dump.py <pyc> <out_txt>
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

pyc, out_path = sys.argv[1], sys.argv[2]
out = open(out_path, 'w', encoding='utf-8')


def log(m):
    out.write(m + '\n')
    out.flush()


from core.cfg import region_analyzer as RA  # noqa: E402
from core.cfg.region_analyzer import MatchRegion  # noqa: E402

_orig = RA.RegionAnalyzer._collect_nested_literal_match


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


def wrap(self, subject_block, parent_blocks, exclude_blocks):
    r = _orig(self, subject_block, parent_blocks, exclude_blocks)
    log('collect_lit subject=%s -> %s' % (
        getattr(subject_block, 'start_offset', None),
        None if r is None else 'REGION'))
    if r is not None:
        log('  case_blocks=%s' % offs(r.case_blocks))
        log('  case_patterns=%r' % (r.case_patterns,))
        log('  case_guards=%r' % (r.case_guards,))
        log('  case_bodies=%s' % [offs(b) for b in r.case_bodies])
        log('  merge=%s blocks=%s' % (getattr(r.merge_block, 'start_offset', None), offs(r.blocks)))
    return r


RA.RegionAnalyzer._collect_nested_literal_match = wrap

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(pyc)
with open(os.path.join(HERE, '_r5_v2_dump_ok.py'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
log('=== DONE ===')
out.close()
