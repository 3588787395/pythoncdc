# -*- coding: utf-8 -*-
"""diag1b: sys.settrace probe on the R47 consumption-point guard inside the
analyzer's ternary-pattern detector (region_analyzer.py L22600-22605).

Read-only: imports the live repo analyzer, analyses ONE code object, and prints
for every candidate diamond the (cond, true, false, merge, value_target,
jump_forward_skip) structural fields plus whether the guard rejected it.

usage: python -X utf8 ctr_r47.py <pyc> <funcname> [lo hi ...]
"""
import io
import marshal
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os_chdir = r'F:/Downloads/pythoncdc-main'
import os
os.chdir(os_chdir)

GUARD = 22600      # `if (merge_block is None and value_target is None ...`
RET = 22603        # `return None`  (guard fired)
PASS = 22605       # `_detect_ternary_context(...)` (guard passed)


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal %s' % path)


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def o(b):
    return getattr(b, 'start_offset', None)


def trace(frame, event, arg):
    if frame.f_code.co_filename.replace('\\', '/').endswith('cfg/region_analyzer.py'):
        if event == 'line' and frame.f_lineno in (GUARD, PASS):
            L = frame.f_locals
            blk = L.get('block')
            tb, fb = L.get('true_block'), L.get('false_block')
            mb = L.get('merge_block')
            rec.append((frame.f_lineno, o(blk), o(tb), o(fb), o(mb),
                        L.get('value_target'), bool(L.get('has_jump_forward_skip')),
                        L.get('merge_context')))
    return trace


rec = []
pyc, name = sys.argv[1], sys.argv[2]
c = [x for x in walk(load_pyc(pyc), []) if x.co_name == name][0]
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
cfg = build_cfg(c)
gen = RegionASTGenerator(cfg, top_level_code=None)
sys.settrace(trace)
try:
    regions = gen.region_analyzer.analyze()
finally:
    sys.settrace(None)

want = set(int(x) for x in sys.argv[3:])
print('# candidates seen: %d  (guard@22600 hit=%d passed=%d)'
      % (len(rec), sum(1 for r in rec if r[0] == GUARD), sum(1 for r in rec if r[0] == PASS)))
print('%-6s %-6s %-6s %-6s %-7s %-10s %-4s %s' %
      ('line', 'cond', 'true', 'false', 'merge', 'value_tgt', 'jfs', 'merge_context'))
for r in rec:
    if want and r[1] not in want and r[2] not in want:
        continue
    tag = 'REJECT' if r[0] == GUARD else 'pass  '
    print('%-6s %-6s %-6s %-6s %-7s %-10s %-4s %-12s %s' % (
        tag, r[1], r[2], r[3], r[4], r[5], r[6], r[7], ''))
print()
print('TERMINAL REGIONS for %s:' % name)
for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
    print('  %s@%s blocks=%s' % (type(r).__name__, o(r.entry),
                                 sorted(o(b) for b in (r.blocks or []))))
