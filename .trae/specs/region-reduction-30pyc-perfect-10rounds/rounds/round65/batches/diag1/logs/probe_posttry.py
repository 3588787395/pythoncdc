# -*- coding: utf-8 -*-
"""diag1 R65 probe: what does _generate_try see as post-try blocks / body tail?

usage: python -X utf8 logs/probe_posttry.py <pyc> <funcname>
Read-only: monkeypatches in-memory only, never writes the repo.
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')


def load_pyc(p):
    d = io.open(p, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(d[off:])
        except Exception:
            continue
    raise SystemExit('bad pyc')


def walk(c, o):
    o.append(c)
    for x in c.co_consts:
        if isinstance(x, types.CodeType):
            walk(x, o)
    return o


def stype(x):
    if isinstance(x, dict):
        return x.get('type', '?')
    return type(x).__name__


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator

    o = lambda b: getattr(b, 'start_offset', None)
    FRAMES = []

    def local(frame, event, arg):
        if event == 'return' and frame.f_code.co_name == '_generate_try':
            loc = frame.f_locals
            reg = loc.get('region')
            if reg is None:
                return
            ptb = loc.get('_post_try_blocks_r19n2') or []
            ta = loc.get('try_ast')
            FRAMES.append(dict(
                entry=o(reg.entry),
                try_end=getattr(reg, 'try_offset_end', None),
                handlers=[o(b) for b in (getattr(reg, 'handler_entry_blocks', None) or [])],
                post_try=[o(b) for b in ptb],
                post_try_htn=[bool(getattr(RegionASTGenerator, '_noop', None) is None and True) for b in ptb][:0],
                try_ast_shape=[stype(x) for x in (ta if isinstance(ta, list) else [ta])] if ta is not None else None,
                body=[stype(x) for x in (loc.get('body_stmts') or [])][-6:],
            ))
        return local

    def tracer(frame, event, arg):
        if event == 'call' and frame.f_code.co_name in ('_generate_try',):
            return local
        return None

    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg)
    sys.settrace(tracer)
    try:
        ast = gen.generate()
    finally:
        sys.settrace(None)
    an = gen.region_analyzer
    for f in FRAMES:
        print('TRY@%-6s try_end=%-6s handlers=%s post_try=%s try_ast=%s body_tail=%s' % (
            f['entry'], f['try_end'], f['handlers'], f['post_try'],
            f['try_ast_shape'], f['body']))
        for off in f['post_try']:
            blk = None
            for b in cfg.blocks.values():
                if b.start_offset == off:
                    blk = b
                    break
            r = an.block_to_region.get(blk) if blk is not None else None
            print('     postblk@%-6s instrs=%s region=%s htn=%s succ=%s' % (
                off, [(i.opname, i.argval) for i in (blk.instructions if blk else [])],
                (type(r).__name__ + '@' + str(o(r.entry))) if r else None,
                getattr(r, 'has_trailing_return_none', None) if r else None,
                [o(s) for s in (blk.successors if blk else [])]))
    print()
    print('ALL REGIONS with has_trailing_return_none:')
    for r in an.regions:
        if getattr(r, 'has_trailing_return_none', False):
            print('   %-16s entry=%-6s parent=%s blocks=%s' % (
                type(r).__name__, o(r.entry),
                (type(r.parent).__name__ + '@' + str(o(r.parent.entry))) if r.parent else None,
                [o(b) for b in r.blocks]))


if __name__ == '__main__':
    main()
