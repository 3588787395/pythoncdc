# -*- coding: utf-8 -*-
"""R67-diag2 read-only probe: CFG blocks/edges + region membership for one function.

usage: python -X utf8 probe_r67.py <pyc> <func>
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('bad pyc')


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def o(b):
    return getattr(b, 'start_offset', None)


pyc, name = sys.argv[1], sys.argv[2]
cs = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
code = cs[0]
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
regions = gen.region_analyzer.analyze()

print('== BLOCKS (%d) ==' % len(cfg.blocks))
for b in sorted(cfg.blocks, key=lambda x: (o(x) if o(x) is not None else -1)):
    succs = [o(s) for s in (getattr(b, 'successors', None) or [])]
    preds = [o(s) for s in (getattr(b, 'predecessors', None) or [])]
    print('  blk %-6s end=%-6s succs=%s preds=%s ninstr=%s'
          % (o(b), getattr(b, 'end_offset', getattr(b, 'last_offset', '?')), succs, preds,
             getattr(b, 'num_instructions', lambda: '?')() if callable(getattr(b, 'num_instructions', None)) else getattr(b, 'instr_count', '?')))

print('== REGION PARENTAGE (%d) ==' % len(regions))
for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
    p = getattr(r, 'parent', None)
    mem = sorted(o(x) for x in (r.blocks or [])) if r.blocks else []
    print('  %-16s entry=%-6s parent=%-18s blocks=%s'
          % (type(r).__name__, o(r.entry),
             ('%s@%s' % (type(p).__name__, o(p.entry))) if p is not None else 'TOP',
             mem))

print('== COVERAGE (blocks claimed by >=1 region) ==')
claimed = {}
for r in regions:
    for b in (r.blocks or []):
        claimed.setdefault(o(b), []).append('%s@%s' % (type(r).__name__, o(r.entry)))
for b in sorted(cfg.blocks, key=lambda x: (o(x) if o(x) is not None else -1)):
    k = o(b)
    print('  blk %-6s -> %s' % (k, claimed.get(k, 'UNCLAIMED')))
