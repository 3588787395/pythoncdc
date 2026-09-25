# -*- coding: utf-8 -*-
"""diag4 r67: per-block CFG + role + region view of one function (live landed analyzer, read-only).
usage: python -X utf8 bdisp.py <pyc> <funcname> [--blocks=80,78]
"""
import io
import marshal
import os
import sys
import types

REPO = r'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(REPO)


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


pyc, name = sys.argv[1], sys.argv[2]
kw = dict(x[2:].split('=', 1) for x in sys.argv[3:])
only = [int(z) for z in kw.get('blocks', '').split(',')] if kw.get('blocks') else None
cs = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

for c in cs:
    cfg = build_cfg(c)
    gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
    ra = gen.region_analyzer
    regions = ra.analyze()
    print('=== %s  blocks=%d regions=%d ===' % (name, len(cfg.blocks), len(regions)))
    blk = list(cfg.blocks.values()) if isinstance(cfg.blocks, dict) else list(cfg.blocks)
    for b in sorted(blk, key=lambda x: x.start_offset):
        if only and b.start_offset not in only:
            continue
        role = ra.get_block_role(b)
        regions_of = [r for r in regions if b in (getattr(r, 'blocks', None) or [])]
        ops = ' | '.join('%s@%s %s' % (i.opname, getattr(i, 'offset', '?'),
                                       str(getattr(i, 'argval', ''))[:18])
                         for i in b.instructions)

        def _so(seq):
            out = []
            for q in (seq or []):
                out.append(q if isinstance(q, int) else getattr(q, 'start_offset', '?'))
            return out
        print('B%-5s role=%-22s lh=%-5s succ=%s preds=%s' % (
            b.start_offset, role, getattr(b, 'loop_header', False),
            _so(getattr(b, 'successors', None)), _so(getattr(b, 'predecessors', None))))
        print('      regions=%s' % [('%s@%s' % (type(r).__name__, r.entry.start_offset)) for r in regions_of])
        print('      %s' % ops[:300])
