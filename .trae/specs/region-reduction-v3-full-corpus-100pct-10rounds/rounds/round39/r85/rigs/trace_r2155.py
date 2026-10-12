"""R21-55 line-intersect ablation: record every line the analyzer's `_detect_ternary_pattern`
executes for a chosen candidate block, plus what it returned — i.e. pin the rejecting predicate
the way R21-33's emitting line was pinned at 13415.

usage: python -X utf8 work/trace_r2155.py <abs pyc> <co-name> <offset> [<offset> ...]
Read-only: no pipeline file is modified.
"""
import os
import sys

MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)

PYC = sys.argv[1]
CONAME = sys.argv[2]
TARGETS = set(int(x) for x in sys.argv[3:])

import linecache
from collections import defaultdict
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
import core.cfg.region_analyzer as an
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

ANALYZER_FILE = os.path.abspath(an.__file__)
SNAP_LINES = {26141, 25996, 24276, 24278, 24282}
SNAP_KEYS = ('true_block', 'false_block', 'merge_block', 'value_target',
             'has_jump_forward_skip', 'merge_context', 'chain_blocks',
             '_consumer_extra_blocks', 'nested_ternary_regions',
             'nested_boolop_regions', 'container_type', 'block', 'candidate_blocks')
SNAP = {}
LINES = defaultdict(list)
RETURNS = defaultdict(list)


def _cand(frame):
    for nm in ('block', 'header', 'cond_block', 'blk'):
        o = getattr(frame.f_locals.get(nm), 'start_offset', None)
        if isinstance(o, int):
            return o
    p = frame.f_locals.get('pattern')
    if isinstance(p, dict):
        return getattr(p.get('condition_block'), 'start_offset', None)
    return None


def make_step(off):
    def step(frame, event, arg):
        if frame.f_code.co_filename != ANALYZER_FILE:
            return None
        if event == 'line':
            LINES[off].append((frame.f_code.co_name, frame.f_lineno))
            if frame.f_lineno in SNAP_LINES and off in TARGETS:
                fl = frame.f_locals
                SNAP[off] = {k: (getattr(fl[k], 'start_offset', None) if hasattr(fl.get(k), 'start_offset')
                                 else (repr(fl[k])[:120] if not isinstance(fl[k], (list, tuple, set)) else
                                       [getattr(x, 'start_offset', x) for x in fl[k]][:8]))
                             for k in SNAP_KEYS if k in fl}
            return step
        if event == 'call':
            return step
        if event == 'return':
            r = arg
            rs = repr(r)[:70] if isinstance(r, (bool, str, int, type(None))) else type(r).__name__
            RETURNS[off].append((frame.f_code.co_name, rs))
            return step
        return step
    return step


def dispatch(frame, event, arg):
    if event != 'call' or frame.f_code.co_filename != ANALYZER_FILE:
        return None
    if frame.f_code.co_name != '_detect_ternary_pattern':
        return None
    o = _cand(frame)
    if o not in TARGETS:
        return None
    return make_step(o)(frame, event, arg)


orig_analyze = RegionAnalyzer.analyze
def analyze(self, *a, **kw):
    if self.cfg.name != CONAME:
        return orig_analyze(self, *a, **kw)
    sys.settrace(dispatch)
    try:
        return orig_analyze(self, *a, **kw)
    finally:
        sys.settrace(None)


RegionAnalyzer.analyze = analyze

mod = load_pyc_file_v2(PYC)
code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()
cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
gen.generate()

print('=== %s: ternary-candidate walk for offsets %s ===' % (CONAME, sorted(TARGETS)))
for o in sorted(TARGETS):
    top = [r for r in RETURNS[o] if r[0] == '_detect_ternary_pattern']
    print('---- @%s  returns=%s  (%d line events)' % (o, top, len(LINES[o])))
    lns = [l for (f, l) in LINES[o] if f == '_detect_ternary_pattern']
    print('  last pattern lines executed:')
    for ln in lns[-9:]:
        print('    %5d  %s' % (ln, linecache.getline(ANALYZER_FILE, ln).rstrip()[:130]))
    if o in SNAP:
        print('  locals at rejection:')
        for k, v in SNAP[o].items():
            print('    %-26s %s' % (k, v))
    seen = set()
    print('  inner returns (unique):')
    for f, r in RETURNS[o]:
        if f == '_detect_ternary_pattern' or (f, r) in seen:
            continue
        seen.add((f, r))
        print('    %-42s -> %s' % (f, r))
