# -*- coding: utf-8 -*-
"""Dump the region ownership around a byte-offset window of one pyc function.

usage: python -X utf8 probe52.py <pyc-rel> <fn-name> <offset>
"""
import io
import json
import marshal
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
BASE = os.environ.get('CORE_BASE', REPO)
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, BASE)
sys.path.insert(0, REPO)

from core.cfg import build_cfg, CFGRegionAnalyzer  # noqa: E402


def find_code(code, name):
    if code.co_name == name:
        return code
    for k in code.co_consts:
        if hasattr(k, 'co_name'):
            r = find_code(k, name)
            if r is not None:
                return r
    return None


rel, fn, off = sys.argv[1], sys.argv[2], int(sys.argv[3])
pyc = os.path.join(REPO, 'site-packages', rel.replace('/', os.sep))
with open(pyc, 'rb') as f:
    f.read(16)
    top = marshal.load(f)
co = find_code(top, fn)
assert co is not None, 'function not found'
cfg = build_cfg(co)
an = CFGRegionAnalyzer(cfg)

TRACE = os.environ.get('TRACE_BUILDERS')
if TRACE:
    for _m in ('_build_basic_if_region', '_build_elif_region'):
        _orig = getattr(CFGRegionAnalyzer, _m)

        def _make(orig=_m, fn=None):
            def wrap(self, block, then_blocks, else_blocks, merge, *a, **k):
                e = getattr(block, 'start_offset', None)
                if e in [int(x) for x in TRACE.split(',')]:
                    r = fn(self, block, then_blocks, else_blocks, merge, *a, **k)
                    print('BUILDER %s entry=%s then=%s else=%s merge=%s -> rt=%s rthen=%s relese=%s rmerge=%s'
                          % (orig, e, sorted(b.start_offset for b in then_blocks),
                             sorted(b.start_offset for b in else_blocks),
                             getattr(merge, 'start_offset', merge),
                             getattr(r, 'region_type', None),
                             sorted(getattr(r, 'then_blocks', None) or [], key=lambda b: b.start_offset) and
                             sorted(b.start_offset for b in (r.then_blocks or [])),
                             sorted(b.start_offset for b in (getattr(r, 'else_blocks', None) or [])),
                             getattr(getattr(r, 'merge_block', None), 'start_offset', None)),
                          flush=True)
                    return r
                return fn(self, block, then_blocks, else_blocks, merge, *a, **k)
            return wrap

        setattr(CFGRegionAnalyzer, _m, _make(_m, _orig))

an.analyze()

JUMPS = ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD_NO_INTERRUPT',
         'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE', 'FOR_ITER', 'SEND')


def term(b):
    for i in reversed(b.instructions):
        if i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PUSH_NULL'):
            return '%s %s' % (i.opname, getattr(i, 'argval', ''))
    return '<noisy>'


def owner(b):
    r = an.block_to_region.get(b)
    if r is None:
        return 'None'
    return '%s@%s' % (type(r).__name__, getattr(r.entry, 'start_offset', None))


allb = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
print('blocks in window:')
for b in sorted(allb, key=lambda x: x.start_offset):
    if off - 40 <= b.start_offset <= off + 24:
        print('  B%d %d-%d term=[%s] succ=%s pred=%s owner=%s role=%s'
              % (b.start_offset, b.start_offset, b.end_offset, term(b),
                 sorted(s.start_offset for s in b.successors),
                 sorted(p.start_offset for p in b.predecessors),
                 owner(b), an.get_block_role(b)))

print('regions touching window:')
_rgs = an.regions.values() if isinstance(an.regions, dict) else an.regions
for r in _rgs:
    hits = [b for b in r.blocks if off - 60 <= b.start_offset <= off + 24]
    if not hits:
        continue
    d = {'type': type(r).__name__, 'rt': str(getattr(r, 'region_type', None)),
         'entry': getattr(r.entry, 'start_offset', None),
         'blocks': sorted(b.start_offset for b in r.blocks),
         'parent': getattr(getattr(r, 'parent', None), 'start_offset', None),
         'merge': getattr(getattr(r, 'merge_block', None), 'start_offset', None)}
    for k in ('condition_block', 'then_blocks', 'else_blocks', 'elif_conditions',
              'elif_final_else', 'try_blocks', 'handler_blocks'):
        if hasattr(r, k):
            v = getattr(r, k)
            if isinstance(v, list):
                d[k] = sorted(getattr(b, 'start_offset', b) for b in v)
            else:
                d[k] = getattr(v, 'start_offset', v)
    print('  ' + json.dumps(d, default=str))
