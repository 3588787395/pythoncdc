# -*- coding: utf-8 -*-
"""diag5 in-memory validation of the two R65-D5 criteria on one function.

Applies the two candidate predicates via monkeypatching (repo untouched) and reports
the official bytecode_diff tuple before/after.

usage: python -X utf8 r65d5_probe.py <pyc> <funcname> [--both|--a|--b]
"""
import io
import json
import marshal
import os
import subprocess
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')
REPO = r'F:/Downloads/pythoncdc-main'


def lp(p):
    d = io.open(p, 'rb').read()
    for o in (16, 12, 8):
        try:
            return marshal.loads(d[o:])
        except Exception:
            pass


def walk(c, out):
    out.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, out)
    return out


MODE = sys.argv[4] if len(sys.argv) > 4 else '--both'
pyc, fname = sys.argv[1], sys.argv[2]
code = [c for c in walk(lp(pyc), []) if c.co_name == fname][0]

from core.cfg import build_cfg
import core.cfg.region_ast_generator as GM
from core.cfg.region_ast_generator import RegionASTGenerator, IfRegion, BoolOpRegion


def crit_a(self, region):
    """[R65-D5-A] entry == already-generated sibling's merge_block, region owns entry."""
    try:
        if not (self.region_analyzer.block_to_region.get(region.entry) is region):
            return False
        arms = list(region.then_blocks or []) + list(region.else_blocks or [])
        if not any(b not in self.generated_blocks for b in arms):
            return False
        for pr in self.regions:
            if (pr is not region and getattr(pr, 'merge_block', None) is region.entry
                    and id(pr) in self._generated_regions):
                return True
        return False
    except Exception:
        return False


def crit_b(self, region):
    """[R65-D5-B] entry marked generated only by a condition-mode child BoolOpRegion."""
    try:
        if getattr(region.entry, 'start_offset', None) is None:
            return False
        for c in (getattr(region, 'children', None) or []):
            if (isinstance(c, BoolOpRegion) and c.entry is region.entry
                    and not getattr(c, 'value_target', None)
                    and any(b is region.entry for b, _op in (c.op_chain or []))):
                return True
        return False
    except Exception:
        return False


_orig_if = RegionASTGenerator._generate_if
_orig_norm = RegionASTGenerator._if_generate_normal

STATS = {'a_fires': 0, 'b_fires': 0}


def _generate_if(self, region):
    if (MODE in ('--a', '--both') and isinstance(region, IfRegion)
            and region.entry in self.generated_blocks
            and crit_a(self, region)):
        if self._boolop_merge_owner_for(region, include_generating=True,
                                        include_generated=True) is None:
            STATS['a_fires'] += 1
            for r in self.regions:
                if (r is not region and isinstance(r, IfRegion)
                        and getattr(r, 'elif_conditions', None)
                        and region.entry in r.elif_conditions):
                    return _orig_if(self, region)
            _w = self._detect_if_region_as_while_loop(region)
            if _w is not None:
                return _w
            return self._if_generate_normal(region)
    return _orig_if(self, region)


def _if_generate_normal(self, region):
    if MODE in ('--b', '--both'):
        _saved = set(self.generated_blocks)
        if crit_b(self, region):
            self.generated_blocks.discard(region.entry)
            STATS['b_fires'] += 1
        try:
            r = _orig_norm(self, region)
        finally:
            pass
        return r
    return _orig_norm(self, region)


RegionASTGenerator._generate_if = _generate_if
RegionASTGenerator._if_generate_normal = _if_generate_normal

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg)
ast = gen.generate()
print('FIRES', MODE, STATS)

# render + official diff
out = os.path.join(r'D:/Temp/opencode/r65gate/diag5', 'probe_out.py')
src = GM.__dict__.get('_r65_dummy', None)
import ast as _ast
mod = {'type': 'Module', 'body': [ast], 'lineno': 1, 'col_offset': 0}
try:
    from core.codegen import ASTCodeGenerator
except Exception:
    ASTCodeGenerator = None
# use pycdc's own emitter
sys.path.insert(0, REPO)
import pycdc
text = pycdc._render_single_function(ast) if hasattr(pycdc, '_render_single_function') else None
if text is None:
    # fall back: build a module AST and unparse via the repo's generator
    from core.cfg.region_ast_generator import RegionASTGenerator as R
    import importlib
    em = importlib.import_module('core.ast_unparser') if importlib.util.find_spec('core.ast_unparser') else None
    print('NOTE: rendering via pycdc.decompile on the whole file instead')
    text = pycdc.decompile_pyc(pyc)
    io.open(out, 'w', encoding='utf-8').write(text)
    import importlib.util as iu
    _s = iu.spec_from_file_location('pbv', os.path.join(REPO, 'scripts', 'pyc_batch_verify.py'))
    pbv = iu.module_from_spec(_s)
    _s.loader.exec_module(pbv)
    rr = pbv.bytecode_diff(pyc, out)
    for m in rr['mismatches']:
        if m['name'] == fname:
            print('OFFICIAL', fname, [m['orig_count'], m['decomp_count'], m['jump_diffs'], m['true_diffs']])
    print('FILE %d/%d' % (rr['matched_functions'], rr['total_functions']))
