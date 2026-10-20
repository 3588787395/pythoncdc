# -*- coding: utf-8 -*-
"""R5 B70e-b trace: locate the emission site of the wrong `continue` in g4b_wt_nested_with."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

out = open(os.path.join(HERE, '_r5_b70e_nested_trace.txt'), 'w', encoding='utf-8')


def w(s):
    out.write(str(s) + '\n')


from core.pyc_loader_v2 import load_pyc_file_v2  # noqa: E402
from core.cfg import build_cfg  # noqa: E402
import core.cfg.region_ast_generator as rag  # noqa: E402
import core.cfg.region_analyzer as ran  # noqa: E402

G = rag.RegionASTGenerator
RA = ran.RegionAnalyzer


def _bo(b):
    return b.start_offset if b is not None else None


_orig_filter = G._filter_if_blocks_in_with


def filter_traced(self, if_region, with_region):
    r = _orig_filter(self, if_region, with_region)
    w('FILTER_IF if@%s(with@%s): then=%s else=%s -> ft=%s fe=%s fb=%s fc=%s' % (
        _bo(if_region.entry), _bo(with_region.entry),
        [_bo(b) for b in if_region.then_blocks], [_bo(b) for b in if_region.else_blocks],
        [_bo(b) for b in r[0]], [_bo(b) for b in r[1]], r[2], r[3]))
    return r


G._filter_if_blocks_in_with = filter_traced

_orig_ltb = RA._is_with_exit_leading_to_break


def ltb_traced(self, block, loop, visited=None):
    r = _orig_ltb(self, block, loop, visited)
    w('LEADING_TO_BREAK blk@%s loop@%s -> %s' % (
        _bo(block), _bo(getattr(loop, 'entry', None)), r))
    return r


RA._is_with_exit_leading_to_break = ltb_traced

_orig_ltc = RA._is_with_exit_leading_to_continue


def ltc_traced(self, block, loop, visited=None):
    r = _orig_ltc(self, block, loop, visited)
    w('LEADING_TO_CONTINUE blk@%s loop@%s -> %s' % (
        _bo(block), _bo(getattr(loop, 'entry', None)), r))
    return r


RA._is_with_exit_leading_to_continue = ltc_traced

_orig_ph = G._break_continue_arm_is_placeholder


def ph_traced(self, then_body):
    r = _orig_ph(self, then_body)
    w('ARM_IS_PLACEHOLDER %s -> %s' % (
        json.dumps(then_body, ensure_ascii=False, default=str)[:200], r))
    return r


G._break_continue_arm_is_placeholder = ph_traced

_orig_gr = G._generate_region


def gr_traced(self, region, **kw):
    r = _orig_gr(self, region, **kw)
    w('GENERATE_REGION %s@%s -> %s' % (
        type(region).__name__, _bo(getattr(region, 'entry', None)),
        json.dumps(r, ensure_ascii=False, default=str)[:300]))
    return r


G._generate_region = gr_traced

module = load_pyc_file_v2(r'test_repros\round5\rec1_synth_g4b_b70_whiletrue_with.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
actual = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
cfg = build_cfg(actual)
gen = RegionASTGenerator = G(cfg, top_level_code=actual if actual.co_name == '<module>' else None)
ast_dict = gen.generate()


def find_func(node, name):
    if isinstance(node, dict):
        if node.get('type') == 'FunctionDef' and node.get('name') == name:
            return node
        for v in node.values():
            r = find_func(v, name)
            if r is not None:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find_func(v, name)
            if r is not None:
                return r
    return None


w('=' * 60)
w('nested_with AST:')
w(json.dumps(find_func(ast_dict, 'g4b_wt_nested_with'), ensure_ascii=False, indent=1, default=str))
out.close()
print('done')
