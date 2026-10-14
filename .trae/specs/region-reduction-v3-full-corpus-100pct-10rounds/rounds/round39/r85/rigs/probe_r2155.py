"""R21-55 probe: what region covers _process_order's ternary blocks, and which builder emits the
empty-arm skeleton?

Runs the real pipeline (build_cfg -> RegionASTGenerator.generate) on the pyc, hooks
  - RegionASTGenerator.generate  (to grab self.regions for the target code object)
  - RegionASTGenerator._generate_region (record dispatch order + result for regions touching the site)
  - the ternary builders named below (record fire / decline)
Prints a per-site report. Read-only: nothing is modified.

usage: python -X utf8 work/probe_r2155.py <abs pyc> <co-name> [lo hi ...]
"""
import marshal
import os
import sys
import types

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)

PYC = sys.argv[1]
CONAME = sys.argv[2]
SITE = [(int(sys.argv[i]), int(sys.argv[i + 1])) for i in range(3, len(sys.argv), 2)]

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_ast_generator as rag
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import IfRegion, TernaryRegion, BoolOpRegion, LoopRegion

mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()

REGIONS = {}
TRACE = []


def _b(blk):
    return getattr(blk, 'start_offset', None)


orig_generate = RegionASTGenerator.generate
def generate(self, *a, **kw):
    out = orig_generate(self, *a, **kw)
    if self.cfg.name == CONAME:
        REGIONS[CONAME] = list(self.regions)
    return out


def site_hit(bl):
    if bl is None:
        return False
    o = _b(bl)
    for lo, hi in SITE:
        if lo <= o <= hi:
            return True
    return False


def region_site(r):
    hits = [ _b(x) for x in (getattr(r, 'blocks', None) or []) if site_hit(x)]
    return hits


orig_gr = RegionASTGenerator._generate_region
def _generate_region(self, region, *a, **kw):
    hits = region_site(region)
    res = orig_gr(self, region, *a, **kw)
    if hits:
        n = len(res) if isinstance(res, list) else (1 if res else 0)
        TRACE.append('_generate_region %s@%s hits=%s -> %d stmts' % (
            type(region).__name__, _b(region.entry), hits, n))
    return res


# hook every ternary-side builder to see which one produced the statement
HOOKS = [
    '_generate_ternary', '_ternary_host_call_prefix_span',
    '_generate_host_prefix_ternary_statement',
    '_try_wrap_fstring_pending_call', '_try_build_ternary_kwarg_call',
    '_try_build_ternary_merge_consumer_expr', '_build_ternary_value_expr',
    '_if_generate_normal', '_generate_if_region', '_try_build_ternary_store_assign',
    '_try_build_ternary_chained_container', '_try_build_andor_boolop_from_ternary',
]

RegionASTGenerator.generate = generate
RegionASTGenerator._generate_region = _generate_region
for name in HOOKS:
    fn = getattr(RegionASTGenerator, name, None)
    if fn is None:
        print('NOTE missing method', name)
        continue

    def mk(_name, _fn):
        def wrapper(self, region, *a, **kw):
            r = _fn(self, region, *a, **kw)
            hits = region_site(region)
            if hits:
                TRACE.append('  %s(%s@%s) hits=%s -> %s' % (
                    _name, type(region).__name__, _b(getattr(region, 'entry', None)), hits,
                    'None' if r is None else ('list[%d]' % len(r) if isinstance(r, list) else
                                              type(r).__name__ if not isinstance(r, tuple) else 'tuple%f' % 0)))
            return r
        return wrapper

    setattr(RegionASTGenerator, name, mk(name, fn))

topcfg = build_cfg(code)
gen = RegionASTGenerator(topcfg, top_level_code=code if code.co_name == '<module>' else None)
ast_dict = gen.generate()

print('=== regions of %s (types) ===' % CONAME)
for r in REGIONS.get(CONAME, []):
    print('%-28s @%-6s blocks=%s site=%s' % (
        type(r).__name__, _b(r.entry), [_b(x) for x in (getattr(r, 'blocks', None) or [])][:20],
        region_site(r)))

print()
print('=== regions touching the site ===')
for r in REGIONS.get(CONAME, []):
    hits = region_site(r)
    if not hits:
        continue
    print('--- %s @%s' % (type(r).__name__, _b(r.entry)))
    for attr in ('condition_block', 'then_blocks', 'else_blocks', 'merge_block',
                 'true_value_block', 'false_value_block', 'entry', 'header_block',
                 'elif_conditions', 'elif_bodies', 'elif_final_else',
                 'region_type', 'value_target', 'container_type', 'merge_context',
                 'inline_boolop_chains'):
        if hasattr(r, attr):
            v = getattr(r, attr)
            if attr=='parent':
                v=_b(v)
            if isinstance(v, (list, tuple)):
                v = [_b(x) if hasattr(x, 'start_offset') else x for x in v]
                v = str(v)[:150]
            elif hasattr(v, 'start_offset'):
                v = _b(v)
            print('    %-22s %s' % (attr, v))

print()
print('=== trace (dispatch order, filtered to site-touching) ===')
for t in TRACE:
    print(t)
