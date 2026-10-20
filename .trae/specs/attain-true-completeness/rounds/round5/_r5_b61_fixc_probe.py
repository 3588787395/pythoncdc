# -*- coding: utf-8 -*-
"""R5 B61 fix(c) probe: did the virtual condition swap fire for the
r8_dh_match_multi IfRegion@30? Logs _generate_if / _if_generate_normal /
_collect_case_capture_names calls during full decompile."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

_orig_gen_if = RegionASTGenerator._generate_if


def _probe_gen_if(self, region):
    try:
        e = getattr(region, 'entry', None)
        c = getattr(region, 'condition_block', None)
        if e is not None and e.start_offset in (30,):
            print('GEN_IF entry=%s cond=%s blocks=%s then=%s n_cond_instrs=%s' % (
                e.start_offset,
                c.start_offset if c is not None else None,
                [b.start_offset for b in getattr(region, 'blocks', [])],
                [b.start_offset for b in getattr(region, 'then_blocks', []) or []],
                len(c.instructions) if c is not None else None))
    except Exception as ex:
        print('GEN_IF probe err %r' % (ex,))
    return _orig_gen_if(self, region)


RegionASTGenerator._generate_if = _probe_gen_if

_orig_ifn = RegionASTGenerator._if_generate_normal


def _probe_ifn(self, region):
    c = region.condition_block
    if c is not None and c.start_offset in (30, 13, 60):
        print('IFNORM cond=%s n_instrs=%s ops=%s' % (
            c.start_offset, len(c.instructions),
            [i.opname for i in c.instructions]))
    return _orig_ifn(self, region)


RegionASTGenerator._if_generate_normal = _probe_ifn

_orig_ccn = RegionASTGenerator._collect_case_capture_names


def _probe_ccn(self, pattern, names):
    r = _orig_ccn(self, pattern, names)
    print('CAPNAMES ptype=%s names=%s' % (
        pattern.get('type') if isinstance(pattern, dict) else pattern,
        sorted(names)))
    return r


RegionASTGenerator._collect_case_capture_names = _probe_ccn

from pycdc import decompile_pyc  # noqa: E402

src = decompile_pyc(r'test_repros\round8\r8_09_deep_host_combo.pyc')
print('=== probe done ===')
