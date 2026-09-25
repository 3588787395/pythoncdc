# -*- coding: utf-8 -*-
"""diag5 line tracer: run the LIVE repo generator on ONE function and record, per call to a
named method, the executed line numbers inside that method's code object.

usage: python -X utf8 linetrace.py <pyc> <funcname> <entry-offset> <method-substring>
Prints the tail of the executed line trace for the call whose region entry offset matches.
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


def main():
    pyc, name, want_entry, meth = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1
    code = codes[0]

    from core.cfg import build_cfg
    import core.cfg.region_ast_generator as G
    from core.cfg.region_ast_generator import RegionASTGenerator

    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg)
    regions = gen.region_analyzer.analyze()
    target = [r for r in regions
              if getattr(r.entry, 'start_offset', None) == want_entry
              and type(r).__name__ == want_type]
    print('target regions:', [(type(r).__name__, r.start_offset if hasattr(r, 'start_offset') else None) for r in target])

    trace = []
    armed = [False]

    def tracer(frame, event, arg):
        co = frame.f_code
        if meth not in co.co_name:
            return None
        if event == 'call':
            if not armed[0]:
                return None
            if co.co_name == meth:
                return liner
            return None
        return None

    def liner(frame, event, arg):
        if not armed[0]:
            return None
        if event == 'line':
            trace.append(frame.f_lineno)
        elif event == 'return':
            trace.append(('RET', frame.f_lineno, repr(arg)[:120]))
        return liner

    orig = getattr(RegionASTGenerator, meth)

    def wrapper(self, region, *a, **k):
        e = getattr(getattr(region, 'entry', None), 'start_offset', None)
        if e == want_entry:
            armed[0] = True
            del trace[:]
        r = orig(self, region, *a, **k)
        if e == want_entry:
            armed[0] = False
            print('== %s region@%s result=%s' % (meth, e, repr(r)[:200]))
            print('   last 45 lines:', trace[-45:])
        return r

    setattr(RegionASTGenerator, meth, wrapper)
    sys.settrace(tracer)
    try:
        gen.generate()
    finally:
        sys.settrace(None)


want_type = 'IfRegion'
if __name__ == '__main__':
    if len(sys.argv) > 5:
        want_type = sys.argv[5]
    main()
