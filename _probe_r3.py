#!/usr/bin/env python3
"""Round3 临时探针：dump CFG 块 + 追踪 _find_loop_else。用后删除。"""
import sys, os, argparse, dis, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_code(pyc_path, fname=None):
    from core.pyc_loader_v2 import load_pyc_file_v2
    mod = load_pyc_file_v2(pyc_path)
    code = mod.code.get() if hasattr(mod.code, 'get') else mod.code
    if hasattr(code, 'to_python_code'):
        code = code.to_python_code()
    if fname is None:
        return code

    def walk(c):
        for k in c.co_consts:
            if isinstance(k, types.CodeType):
                if k.co_name == fname:
                    return k
                r = walk(k)
                if r is not None:
                    return r
        return None

    r = walk(code)
    if r is None:
        raise SystemExit('code not found: ' + fname)
    return r


def dump_cfg(code):
    from core.cfg import build_cfg
    cfg = build_cfg(code)
    blocks = sorted(cfg.blocks.values(), key=lambda b: b.start_offset)
    for b in blocks:
        last = b.get_last_instruction()
        print('B%d [%d..%d] preds=%s succs=%s exsucc=%s last=%s' % (
            b._id, b.start_offset, b.end_offset,
            sorted(p._id for p in b.predecessors),
            sorted(s._id for s in b.successors),
            sorted(s._id for s in b.exception_successors),
            last.opname if last else None))
        for i in b.instructions:
            print('      %4d: %s %s' % (i.offset, i.opname, i.argval if i.arg is not None else ''))
    return cfg


def trace_find_loop_else(code, funcname):
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer
    cfg = build_cfg(code)
    an = RegionAnalyzer(cfg)
    orig = RegionAnalyzer._find_loop_else

    def wrapped(self, header, loop_body, loop_type, for_iter_exit=None, condition_block=None):
        r = orig(self, header, loop_body, loop_type, for_iter_exit, condition_block)
        print('[FLE] header=B%d type=%s fie=B%s cond=B%s body=%s -> else=%s natural_exit=%s' % (
            header._id, loop_type,
            for_iter_exit._id if for_iter_exit else None,
            condition_block._id if condition_block else None,
            sorted(b._id for b in loop_body),
            [b._id for b in (r[0] or [])],
            r[1]._id if r[1] else None))
        return r

    RegionAnalyzer._find_loop_else = wrapped
    try:
        regions = an.analyze()
    finally:
        RegionAnalyzer._find_loop_else = orig
    for r in regions:
        print('[R] %s blocks=%s hdr=%s body=%s else=%s break=%s has_break=%s natural_exit=%s' % (
            type(r).__name__,
            sorted(b._id for b in getattr(r, 'blocks', []) or []),
            getattr(r, 'header_block', None) and r.header_block._id,
            sorted(b._id for b in getattr(r, 'body_blocks', None) or []),
            sorted(b._id for b in getattr(r, 'else_blocks', None) or []),
            sorted(b._id for b in getattr(r, 'break_blocks', None) or []),
            getattr(r, 'has_break', None),
            getattr(r, 'natural_exit', None) and r.natural_exit._id))
    return an, cfg


def trace_guard(code, funcname):
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer
    cfg = build_cfg(code)
    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    off = {}
    for b in cfg.blocks.values():
        off[b.start_offset] = b._id
    for r in regions:
        name = type(r).__name__
        if name != 'LoopRegion':
            continue
        eb = [b.start_offset for b in (r.else_blocks or [])]
        bb = [b.start_offset for b in (r.break_blocks or [])]
        parents = [pl for pl in regions
                   if type(pl).__name__ == 'LoopRegion' and pl is not r
                   and hasattr(pl, 'body_blocks') and pl.body_blocks
                   and any(b in pl.body_blocks for b in r.body_blocks)]
        trig = any(x not in set(eb) for x in bb) and bool(parents)
        print('[G] hdr=%s off=%s body=%s else=%s break=%s parents=%s TRIGGER=%s' % (
            r.header_block._id, r.header_block.start_offset,
            sorted(b.start_offset for b in r.body_blocks), eb, bb,
            [p.header_block.start_offset for p in parents], trig))
    return an, cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pyc')
    ap.add_argument('--func')
    ap.add_argument('--mode', default='cfg')
    args = ap.parse_args()
    code = load_code(args.pyc, args.func)
    if args.mode == 'cfg':
        dump_cfg(code)
    elif args.mode == 'guard':
        trace_guard(code, args.func)
    else:
        print('--- dis ---')
        dis.dis(code)
        trace_find_loop_else(code, args.func)


if __name__ == '__main__':
    main()
