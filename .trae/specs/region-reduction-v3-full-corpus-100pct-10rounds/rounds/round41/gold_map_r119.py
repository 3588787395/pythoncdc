"""Map the mismatching blocks to GOLD source text.

usage: python -X utf8 gold_map_r119.py <product.py>
GOLD compiles to a clock_worker whose block opname sequence matches the ORIGINAL pyc
element-for-element (1442 instrs / 176 blocks / opseq-match=True), so GOLD line numbers are
a valid source-level view of the original CFG. This prints, for every block signature that
differs between the [R21-90]-class product and GOLD, BOTH source excerpts side by side.
"""
import io
import sys
from collections import Counter

sys.path.insert(0, 'D:/Temp/mon')
from bcore_r118 import find, blocks

ROOT = 'D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/'
GOLD = ROOT + '.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round41/GOLD_realtime_event_source_PROOF.py'
UNIT = 'clock_worker'


def load(p):
    src = io.open(p, encoding='utf-8-sig').read().replace('\r\n', '\n').split('\n')
    c = find(compile(io.open(p, encoding='utf-8-sig').read(), p, 'exec'), UNIT)
    return src, blocks(c), c


def txt(src, b, nxt_line):
    a = b['line'] or 0
    z = nxt_line or a + 1
    return ' | '.join(s.strip() for s in src[a - 1:z - 1] if s.strip())[:150]


def main():
    prod = sys.argv[1]
    gs, gb, gc = load(GOLD)
    ps, pb, pc = load(prod)
    print('GOLD instrs=%d blocks=%d   PROD instrs=%d blocks=%d' %
          (sum(b['n'] for b in gb), len(gb), sum(b['n'] for b in pb), len(pb)))
    print('GOLD-vs-PROD opseq-list-identical=%s' % ([b['sig'] for b in gb] == [b['n'] and b['sig'] for b in pb]))
    gsig, psig = Counter(b['sig'] for b in gb), Counter(b['sig'] for b in pb)
    only_g, only_p = gsig - psig, psig - gsig
    print('SIG-ONLY-GOLD=%d SIG-ONLY-PROD=%d' % (sum(only_g.values()), sum(only_p.values())))

    def lined(src, bs):
        out = []
        for i, b in enumerate(bs):
            nxt = bs[i + 1]['line'] if i + 1 < len(bs) else None
            out.append((b, txt(src, b, nxt)))
        return out

    gl, pl = lined(gs, gb), lined(ps, pb)
    for title, cs, other in (('GOLD-ONLY', only_g, psig), ('PROD-ONLY', only_p, gsig)):
        for sig, n in cs.items():
            for b, t in gl if title == 'GOLD-ONLY' else pl:
                if b['sig'] == sig:
                    print('\n%s  in=%d out=%d n=%d' % (title, b['in'], b['out'], b['n']))
                    print('   ops : %s' % sig[:120])
                    print('   src : %s' % t)
                    break
    return 0


sys.exit(main())
