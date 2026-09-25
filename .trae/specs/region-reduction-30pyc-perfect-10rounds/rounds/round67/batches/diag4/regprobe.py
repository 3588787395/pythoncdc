# -*- coding: utf-8 -*-
"""diag4 r67: dump try/except + enclosing-loop region fields for one function (read-only).
usage: python -X utf8 regprobe.py <pyc> <funcname>
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


def o(b):
    return getattr(b, 'start_offset', b)


pyc, name = sys.argv[1], sys.argv[2]
cs = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

for c in cs:
    cfg = build_cfg(c)
    gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
    ra = gen.region_analyzer
    regions = ra.analyze()
    print('=== %s ===' % name)
    for r in regions:
        t = type(r).__name__
        if 'Loop' in t:
            print('LOOP entry=%s header=%s cond=%s back_edge=%s body=%s exit=%s' % (
                o(r.entry), o(getattr(r, 'header_block', None)), o(getattr(r, 'condition_block', None)),
                o(getattr(r, 'back_edge_block', None)),
                [o(b) for b in (getattr(r, 'body_blocks', None) or [])], o(getattr(r, 'exit', None))))
            hdr = getattr(r, 'header_block', None)
            if hdr is not None:
                print('     header instrs=%s' % [(i.opname, i.offset) for i in hdr.instructions])
        if 'Try' in t:
            print('TRY   entry=%s try=%s handler_entries=%s has_finally=%s' % (
                o(r.entry), [o(b) for b in (getattr(r, 'try_blocks', None) or [])],
                [o(b) for b in (getattr(r, 'handler_entry_blocks', None) or [])],
                getattr(r, 'has_finally', None)))
            for i, h in enumerate(getattr(r, 'except_handlers', None) or []):
                print('      handler[%d] type=%r name=%r blocks=%s' % (
                    i, h[0], h[1], [o(b) for b in (h[2] or [])]))
            for k in ('finalbody_blocks', 'else_blocks', 'cleanup_blocks', 'finally_copy_blocks'):
                v = getattr(r, k, None)
                if v:
                    print('      %s=%s' % (k, [o(b) for b in v]))
        if 'With' in t:
            print('WITH  entry=%s' % o(r.entry))
