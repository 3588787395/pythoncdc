"""Block-signature diff: name the CFG-visible residue without needing aligned line numbers.

usage: python -X utf8 block_diff_r118.py <product.py>
Splits clock_worker in the ORIGINAL pyc and in the product's compiled code object into
basic blocks, signs each block by its opname sequence, prints blocks unique to either
side with in/out degree. Jump targets in dis are already absolute (argval), so edges
are read straight off it.
"""
import dis
import marshal
import sys
import types
from collections import Counter

ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/'
PYC = ROOT + 'site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'
UNIT = 'clock_worker'
JUMPS = ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP', 'RETURN_VALUE', 'RAISE_VARARGS',
         'BREAK', 'CONTINUE', 'END_FOR', 'END_ASYNC_FOR', 'RERAISE', 'EXIT_STACK_RESET')


def find(c, name):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == name:
                return k
            r = find(k, name)
            if r is not None:
                return r
    return None


def blocks(c):
    ins = list(dis.get_instructions(c))
    offs = [i.offset for i in ins]
    oset = set(offs)
    tgt = {}
    for i in ins:
        if i.opcode in dis.hasjrel or i.opcode in dis.hasjabs:
            if isinstance(i.argval, int) and i.argval in oset:
                tgt[i.offset] = i.argval
    leaders = {offs[0]}
    for i in ins:
        if i.offset in tgt:
            leaders.add(tgt[i.offset])
            n = offs.index(i.offset)
            if n + 1 < len(ins):
                leaders.add(offs[n + 1])
        elif any(i.opname.startswith(p) for p in JUMPS):
            n = offs.index(i.offset)
            if n + 1 < len(ins):
                leaders.add(offs[n + 1])
    leaders = sorted(leaders)
    line_of = {}
    for cl in c.co_lines():
        if cl[2] is not None:
            for o in range(cl[0], cl[1], 2):
                line_of[o] = cl[2]

    def lead_of(off):
        lo, hi = 0, len(leaders) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if leaders[mid] <= off:
                lo = mid
            else:
                hi = mid - 1
        return leaders[lo]

    out = []
    for li, start in enumerate(leaders):
        end = leaders[li + 1] if li + 1 < len(leaders) else offs[-1] + 2
        bi = [i for i in ins if start <= i.offset < end]
        if not bi:
            continue
        outs = {lead_of(tgt[i.offset]) for i in bi if i.offset in tgt}
        outs.discard(start)
        out.append(dict(start=start, sig=' '.join(i.opname for i in bi), n=len(bi),
                        line=line_of.get(start), outs=sorted(outs)))
    ind = Counter(t for b in out for t in b['outs'])
    for b in out:
        b['in'] = ind.get(b['start'], 0)
        b['out'] = len(b['outs'])
    return out


def main():
    prod = sys.argv[1]
    o = find(marshal.loads(open(PYC, 'rb').read()[16:]), UNIT)
    p = find(compile(open(prod, encoding='utf-8-sig').read(), prod, 'exec'), UNIT)
    ob, pb = blocks(o), blocks(p)
    oc, pc = Counter(b['sig'] for b in ob), Counter(b['sig'] for b in pb)
    print('blocks orig=%d prod=%d instrs orig=%d prod=%d' %
          (len(ob), len(pb), sum(b['n'] for b in ob), sum(b['n'] for b in pb)))
    only_o, only_p = oc - pc, pc - oc
    print('SIG-ONLY-ORIG=%d SIG-ONLY-PROD=%d' % (sum(only_o.values()), sum(only_p.values())))
    for sig, n in sorted(only_o.items(), key=lambda kv: -kv[1])[:12]:
        b = next(x for x in ob if x['sig'] == sig)
        print('  ORIG-ONLY x%d line=%s in=%d out=%d n=%d :: %s' % (n, b['line'], b['in'], b['out'], b['n'], sig[:100]))
    for sig, n in sorted(only_p.items(), key=lambda kv: -kv[1])[:12]:
        b = next(x for x in pb if x['sig'] == sig)
        print('  PROD-ONLY x%d line=%s in=%d out=%d n=%d :: %s' % (n, b['line'], b['in'], b['out'], b['n'], sig[:100]))
    print('--- degree mismatches on shared signatures (same ops, different edges) ---')
    shown = 0
    for sig in set(oc) & set(pc):
        for b in [x for x in ob if x['sig'] == sig]:
            for c in [x for x in pb if x['sig'] == sig]:
                if (b['in'], b['out']) != (c['in'], c['out']) and shown < 12:
                    print('  orig line=%s (in,out)=%s,%s  prod line=%s %s,%s :: %s'
                          % (b['line'], b['in'], b['out'], c['line'], c['in'], c['out'], sig[:80]))
                    shown += 1
    return 0


sys.exit(main())
