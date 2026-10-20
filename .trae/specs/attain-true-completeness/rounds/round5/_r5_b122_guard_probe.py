# -*- coding: utf-8 -*-
"""R5 B122 守卫提取追踪：log collect_pattern_blocks / parse_case_guard 调用。

用法: python -X utf8 _r5_b122_guard_probe.py <pyc> <out_txt>
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
from core.cfg.pattern_parser import PatternParser  # noqa: E402
from core.cfg.region_analyzer import NOISE_OPS, CONDITIONAL_JUMP_OPS  # noqa: E402

_LOAD_OPS = ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')
_CMP_OPS = ('COMPARE_OP', 'IS_OP')


def self_subject_header(block):
    if block is None:
        return False
    m = [i for i in block.instructions if i.opname not in NOISE_OPS]
    if not m or m[-1].opname not in CONDITIONAL_JUMP_OPS:
        return False
    if any(i.opname == 'COPY' for i in m):
        return False
    if not any(i.opname in _LOAD_OPS for i in m):
        return False
    if not any(i.opname in _CMP_OPS for i in m):
        return False
    return True


_orig_find = RA.RegionAnalyzer._find_nested_match_subject


def patched_find(self, case_block, parent_blocks):
    if self_subject_header(case_block):
        return case_block
    return _orig_find(self, case_block, parent_blocks)


RA.RegionAnalyzer._find_nested_match_subject = patched_find

_orig_collect = PatternParser._collect_pattern_blocks
_orig_guard = PatternParser._extract_case_guard_from_blocks

count = {'collect': 0, 'guard': 0}


def offs(bs):
    return [getattr(b, 'start_offset', None) for b in (bs or [])]


def wrap_collect(self, case_block, all_blocks):
    r = _orig_collect(self, case_block, all_blocks)
    count['collect'] += 1
    log('collect#%d case=%s -> %s' % (count['collect'], getattr(case_block, 'start_offset', None), offs(r)))
    return r


def wrap_guard(self, pattern_blocks, allow_in_header_block=False, fail_case_offset=None):
    count['guard'] += 1
    r = _orig_guard(self, pattern_blocks, allow_in_header_block, fail_case_offset)
    log('guard#%d pb=%s allow=%s fail=%s -> %r' % (
        count['guard'], offs(pattern_blocks), allow_in_header_block, fail_case_offset, r))
    return r


PatternParser._collect_pattern_blocks = wrap_collect
PatternParser._extract_case_guard_from_blocks = wrap_guard

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(pyc)
with open(os.path.join(HERE, '_r5_b122_guardprobe_ok.py'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
log('=== DONE ===')
out.close()
