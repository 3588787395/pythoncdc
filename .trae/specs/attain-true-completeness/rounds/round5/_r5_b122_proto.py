# -*- coding: utf-8 -*-
"""R5 B122 原型：_find_nested_match_subject 增强——候选块自身为链头时直接作 subject。

用法: python -X utf8 _r5_b122_proto.py <pyc> <out_ok.py> [variant=1]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

pyc, ok = sys.argv[1], sys.argv[2]
variant = int(sys.argv[3]) if len(sys.argv) > 3 else 1

from core.cfg import region_analyzer as RA  # noqa: E402
from core.cfg.region_analyzer import CONDITIONAL_JUMP_OPS, NOISE_OPS  # noqa: E402

_LOAD_OPS = ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')
_CMP_OPS = ('COMPARE_OP', 'IS_OP')


def self_subject_header(block):
    """候选块自身即字面量链头（首 case 头且不保留 subject 副本）。"""
    if block is None:
        return False
    m = [i for i in block.instructions if i.opname not in NOISE_OPS]
    if not m:
        return False
    if m[-1].opname not in CONDITIONAL_JUMP_OPS:
        return False
    if any(i.opname == 'COPY' for i in m):
        return False
    if not any(i.opname in _LOAD_OPS for i in m):
        return False
    if not any(i.opname in _CMP_OPS for i in m):
        return False
    return True


_orig = RA.RegionAnalyzer._find_nested_match_subject


def patched(self, case_block, parent_blocks):
    if variant >= 1 and self_subject_header(case_block):
        return case_block
    return _orig(self, case_block, parent_blocks)


RA.RegionAnalyzer._find_nested_match_subject = patched

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(pyc)
with open(ok, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src)
print('OK ->', ok)
