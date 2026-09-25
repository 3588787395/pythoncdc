# -*- coding: utf-8 -*-
"""probe_ternary: trace the LIVE landed analyzer's ternary-detection nested helpers for ONE
function and report, for a chosen condition-block offset, which predicate vetoed the
TernaryRegion.  Repo read-only (sys.settrace only).

usage: python -X utf8 probe_ternary.py <pyc> <funcname> [cond-offset]
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')

NAMES = ('_can_be_ternary_header', '_detect_ternary_pattern', '_is_ternary_block',
         '_detect_ternary_context', '_build_ternary_condition_chain',
         '_try_create_ternary_region', '_is_statement_ternary_entry',
         '_detect_chained_compare_pattern', '_is_chained_compare_header')


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


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    want = int(sys.argv[3]) if len(sys.argv) > 3 else None
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1
    code = codes[0]
    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer

    cfg = build_cfg(code)

    def blk(x):
        try:
            if isinstance(x, int):
                return x
            return o(x)
        except Exception:
            return None

    def trace(frame, event, arg):
        f = frame.f_code
        if f.co_name not in NAMES:
            return None
        if event == 'call':
            a0 = None
            try:
                a0 = blk(frame.f_locals.get('block', frame.f_locals.get('header',
                     frame.f_locals.get('cond_block', frame.f_locals.get('blk')))))
            except Exception:
                pass
            TAGS[id(frame)] = (f.co_name, a0)
            if want is None or a0 == want:
                print('CALL %-30s arg_block=%s' % (f.co_name, a0))
            return trace
        if event == 'return':
            tag = TAGS.pop(id(frame), (f.co_name, None))
            if want is None or tag[1] == want:
                r = arg
                if isinstance(r, tuple):
                    rs = 'tuple(%s)' % ' | '.join(
                        (o(x) if hasattr(x, 'start_offset') else
                         (str(x)[:60] if not isinstance(x, (list, dict)) else
                          ','.join(str(o(y)) for y in (x if isinstance(x, list) else [x]))))
                        for x in r)
                elif isinstance(r, bool):
                    rs = str(r)
                elif r is None:
                    rs = 'None'
                else:
                    rs = repr(r)[:80]
                print('RET  %-30s arg_block=%s -> %s' % (tag[0], tag[1], rs))
            return trace
        return trace

    TAGS = {}
    sys.settrace(trace)
    try:
        regions = RegionAnalyzer(cfg).analyze()
    finally:
        sys.settrace(None)
    print()
    print('ternary regions:', [(o(r.entry), type(r).__name__) for r in regions
                               if 'ernary' in type(r).__name__])
    print('region for block %s: %s' % (want, type(
        RegionAnalyzer(cfg).block_to_region.get(cfg.get_block_by_offset(want))).__name__
        if want is not None else None))


if __name__ == '__main__':
    main()
