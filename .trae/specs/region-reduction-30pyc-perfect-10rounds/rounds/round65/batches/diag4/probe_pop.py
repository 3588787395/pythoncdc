# -*- coding: utf-8 -*-
"""probe_pop: instrument the LIVE landed analyzer's [R64-diag1] chain.pop() site with
sys.settrace (NO repo file is modified) and print every pop that fires while analyzing
ONE function's code object, with the structural state at the moment of the pop.

usage: python -X utf8 probe_pop.py <pyc> <funcname> [lineno ...]
Default pop line = 25601 (repo landed region_analyzer.py).  Pass extra line numbers if
the landed file shifts.
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')

ANALYZER = os.path.join('core', 'cfg', 'region_analyzer.py')
POP_LINE = 25601


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


def lastinfo(b):
    li = b.get_last_instruction() if b is not None else None
    if li is None:
        return 'None'
    return '%s@%d->%s' % (li.opname, li.offset, o(_blk_of(li)))


def _blk_of(instr):
    try:
        from core.cfg.region_analyzer import RegionAnalyzer  # noqa
    except Exception:
        return None
    return None


def chaininfo(chain):
    return ' | '.join('@%s(%s) last=%s' % (o(b), op,
                                           (b.get_last_instruction().opname
                                            + '->' + str(o_of(b))
                                            if b.get_last_instruction() else '?'))
                      for b, op in chain)


def o_of(b):
    li = b.get_last_instruction()
    return li.argval if li is not None and getattr(li, 'argval', None) is not None else None


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    lines = set(int(x) for x in sys.argv[3:]) or {POP_LINE}
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]

    from core.cfg import build_cfg
    from core.cfg.region_analyzer import RegionAnalyzer

    hits = []

    def trace(frame, event, arg):
        f = frame.f_code
        if not f.co_filename.replace('\\', '/').endswith(ANALYZER.replace('\\', '/')):
            return None
        if event == 'line' and f.co_name in ('_detect_boolop_conditional_chain',) \
                and frame.f_lineno in lines:
            try:
                chain = frame.f_locals['chain']
                current = frame.f_locals['current']
                _T = frame.f_locals.get('_r64_T')
                ft = frame.f_locals.get('ft_succ')
                cj = frame.f_locals.get('_r64_cj')
                last = frame.f_locals.get('last')
                sb = frame.f_locals.get('start_block')
                rec = dict(
                    line=frame.f_lineno,
                    start_block=o(sb), current=o(current),
                    chain=[(o(b), op) for b, op in chain],
                    chain_first=o(chain[0][0]) if chain else None,
                    T=o(_T), cj=o(cj), ft=o(ft),
                    T_is_current=(_T is current), cj_is_T=(cj is _T), ft_is_T=(ft is _T),
                    last='%s@%s->%s' % (last.opname, last.offset, last.argval),
                    depth=len(frame.f_back.f_code.co_name) if frame.f_back else 0,
                    caller=frame.f_back.f_code.co_name if frame.f_back else None,
                )
                hits.append(rec)
                print('POP line=%d start_block@%s current@%s chain=%s T@%s cj@%s ft@%s caller=%s' % (
                    rec['line'], rec['start_block'], rec['current'], rec['chain'],
                    rec['T'], rec['cj'], rec['ft'], rec['caller']))
            except Exception as e:
                print('PROBE ERR', repr(e)[:200])
        return trace

    sys.settrace(trace)
    try:
        cfg = build_cfg(code)
        an = RegionAnalyzer(cfg)
        regions = an.analyze()
    finally:
        sys.settrace(None)

    print()
    print('TOTAL POPS AT [R64-diag1] = %d' % len(hits))
    print('REGIONS %d' % len(regions))
    for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
        print('  %-18s entry=%-5s blocks=%s merge=%s' % (
            type(r).__name__, o(r.entry), [o(b) for b in (r.blocks or [])],
            o(getattr(r, 'merge_block', None))))


if __name__ == '__main__':
    main()
