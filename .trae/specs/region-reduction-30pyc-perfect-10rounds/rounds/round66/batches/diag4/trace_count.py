# -*- coding: utf-8 -*-
"""diag4 R66: read-only runtime call counter (sys.settrace, 'call' events only).

Counts every call to top-level/inner functions of the two region files while
decompiling one pyc, and (for a name whitelist) records the def lineno + a
dump of chosen f_locals reprs, so a suspected path can be CONFIRMED or
FALSIFIED with real hit counts.

usage: python -X utf8 trace_count.py <pyc> [--locals=fn_name:key,key:...] [--print=regex]
"""
import io
import json
import os
import re
import sys
import collections

REPO = r'F:\Downloads\pythoncdc-main'
sys.stdout.reconfigure(encoding='utf-8')

TARGETS = ('region_ast_generator.py', 'region_analyzer.py')


def main():
    pyc = sys.argv[1]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[2:])
    localkeys = {}
    for spec in (kw.get('locals') or '').split(';'):
        if spec and ':' in spec:
            fn, keys = spec.split(':', 1)
            localkeys[fn] = keys.split(',')
    pat = kw.get('print')
    retkeys = set(x for x in (kw.get('rets') or '').split(',') if x)
    retkeys = set((kw.get('ret') or '').split(',')) - {''}
    counts = collections.Counter()
    events = []

    sys.path.insert(0, REPO)
    import pycdc

    def trace(frame, event, arg):
        code = frame.f_code
        base = os.path.basename(code.co_filename)
        if base not in TARGETS:
            return None
        interested = code.co_name in localkeys or (pat and re.search(pat, code.co_name))
        retint = code.co_name in retkeys or (pat and re.search(pat, code.co_name))
        if event == 'call':
            counts[(base, code.co_name)] += 1
            if interested:
                info = {'fn': code.co_name, 'file': base, 'lineno': frame.f_lineno}
                try:
                    bk = frame.f_back
                    while bk is not None and os.path.basename(bk.f_code.co_filename) not in TARGETS:
                        bk = bk.f_back
                    if bk is not None:
                        info['caller'] = '%s@%d' % (bk.f_code.co_name, bk.f_lineno)
                except Exception:
                    pass
                for k in localkeys.get(code.co_name, []):
                    try:
                        v = frame.f_locals.get(k)
                        if hasattr(v, 'opname'):
                            v = [x.opname for x in v]
                        info[k] = repr(v)[:700]
                    except Exception as e:
                        info[k] = 'ERR' + repr(e)[:60]
                events.append(info)
            if retint:
                return trace
            return None
        if event == 'return' and retint:
            events.append({'RET': code.co_name, 'lineno': frame.f_lineno,
                           'val': repr(arg)[:700]})
            return None
        return trace

    sys.settrace(trace)
    try:
        text = pycdc.decompile_pyc(pyc)
    finally:
        sys.settrace(None)
    out = text if text else ''
    print('### output lines with suspicious subscript-assign:')
    for l in out.splitlines():
        if re.match(r"^\s*'.*'\[.*\] = ", l):
            print('  ', l)
    print('### TOP CALL COUNTS')
    for (f, n), c in counts.most_common(40):
        print('%-26s %-46s %d' % (f, n, c))
    print('### EVENT DUMPS (%d)' % len(events))
    for e in events:
        print(json.dumps(e, ensure_ascii=False)[:900])


if __name__ == '__main__':
    main()
