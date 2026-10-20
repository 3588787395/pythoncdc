# -*- coding: utf-8 -*-
"""R5 B61 phantom-source probe: find which emitter produces the
`(rest,) = {}` statement for r8_dh_match_multi (block containing
BUILD_MAP + UNPACK_SEQUENCE + STORE_FAST rest)."""
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

_orig_gbs = RegionASTGenerator._generate_block_statements


def _probe_gbs(self, block):
    ops = [i.opname for i in block.instructions]
    if 'BUILD_MAP' in ops and 'UNPACK_SEQUENCE' in ops:
        print('GBS block off=%s ops=%s' % (block.instructions[0].offset if block.instructions else None, ops))
        stack = traceback.extract_stack()[:-1]
        for fr in stack[-8:]:
            print('   %s:%s in %s' % (os.path.basename(fr.filename), fr.lineno, fr.name))
    return _orig_gbs(self, block)


RegionASTGenerator._generate_block_statements = _probe_gbs

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(r'test_repros\round8\r8_09_deep_host_combo.pyc')
print('=== probe done ===')
