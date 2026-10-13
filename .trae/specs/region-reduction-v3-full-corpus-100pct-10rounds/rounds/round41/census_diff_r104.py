"""Judge-side blind spot closer: compare a product's clock_worker code object to the ORIGINAL by
edge structure (jump targets resolved through content alignment), not by blanked instruction text.

usage: python -X utf8 census_diff_r104.py <product.py>
Prints: instr counts, back-edge counts, and the per-target in-degree multisets for original vs product.
Rationale: allwin/win_r91 blank jump operands, so a candidate can read delta=0/hunks=0 while the judge
(compares CFG equivalence first) still fails. This instrument shows WHY in one number.
"""
import compileall  # noqa
import dis
import marshal
import sys
import types

PYC = 'site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'


def find(c, name):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == name:
                return k
            r = find(k, name)
            if r is not None:
                return r
    return None


def sig(opname):
    return ('J' if (opname in dis.hasjrel or opname in dis.hasjabs) else '') + opname


def edges(c):
    ins = list(dis.get_instructions(c))
    offs = sorted({i.offset for i in ins})
    idx = {o: n for n, o in enumerate(offs)}
    su = {}
    for i in ins:
        if i.opcode in dis.hasjrel or i.opcode in dis.hasjabs:
            a = i.argval
            if isinstance(a, int) and a in idx:
                su.setdefault(i.offset, set()).add(a)
    back = sum(1 for o, ts in su.items() if any(t <= o for t in ts))
    indeg = {}
    for o, ts in su.items():
        for t in ts:
            indeg[t] = indeg.get(t, 0) + 1
    seq = tuple(sig(i.opname) for i in ins)
    return dict(n=len(ins), back=back, jsites=len(su),
                indeg=sorted(indeg.values(), reverse=True)[:14],
                top=sorted([(p, o) for o, p in indeg.items()], reverse=True)[:8], seq=seq)


def main():
    prod = sys.argv[1]
    src = open(prod, encoding='utf-8-sig').read()
    pc = find(compile(src, prod, 'exec'), 'clock_worker')
    o = find(marshal.loads(open(PYC, 'rb').read()[16:]), 'clock_worker')
    if pc is None or o is None:
        print('clock_worker NOT FOUND', 'orig' if o is None else '', 'product' if pc is None else '')
        return 1
    a, b = edges(o), edges(pc)
    print('original   instrs=%d back=%d jsites=%d indeg=%s' % (a['n'], a['back'], a['jsites'], a['indeg']))
    print('product    instrs=%d back=%d jsites=%d indeg=%s' % (b['n'], b['back'], b['jsites'], b['indeg']))
    print('DELTAS     instrs=%+d back=%+d jsites=%+d' % (b['n'] - a['n'], b['back'] - a['back'], b['jsites'] - a['jsites']))
    print('indeg-equal=%s back-equal=%s opseq-equal=%s' % (a['indeg'] == b['indeg'], a['back'] == b['back'], a['seq'] == b['seq']))
    print('top original', a['top'])
    print('top product ', b['top'])
    return 0


sys.exit(main())
