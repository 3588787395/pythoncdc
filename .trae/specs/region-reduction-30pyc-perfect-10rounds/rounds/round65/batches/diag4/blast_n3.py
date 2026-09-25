# -*- coding: utf-8 -*-
"""blast_n3: blast-radius for candidate n3 (relax the R24-A CFG-entry exclusion in
IfRegion.can_be_ternary_header when the chained-compare diamond is a real value diamond).

Monkeypatches the LIVE landed analyzer in memory only; repo stays untouched.
For every code object in the list, report blocks where the landed method returns False
purely because `self.entry is analyzer.cfg.entry_block`, and whether n3's structural
value-diamond predicate would let it through.

usage: python -X utf8 blast_n3.py <list.txt> [--out=x.jsonl] [--nshard=N --shard=I]
"""
import io
import json
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
    return None


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def o(b):
    return getattr(b, 'start_offset', None)


NOISE = ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME')


def main():
    listfile = sys.argv[1]
    kw = dict(x[2:].split('=', 1) for x in sys.argv[2:])
    out = kw.get('out')
    nshard = int(kw.get('nshard', 1))
    shard = int(kw.get('shard', 0))
    paths = [l.strip() for l in io.open(listfile, encoding='utf-8') if l.strip()]
    paths = [q for i, q in enumerate(paths) if i % nshard == shard]

    from core.cfg import build_cfg
    import core.cfg.region_analyzer as RA
    from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, FORWARD_CONDITIONAL_JUMP_OPS

    orig = IfRegion.can_be_ternary_header
    hits = []

    def n3_predicate(region, block, analyzer):
        """the Phase-7-D diamond: last chained-compare block's two successors are both
        single-expression value blocks that converge on one merge block."""
        allcc = [region.entry] + list(region.chained_compare_blocks or [])
        last = allcc[-1].get_last_instruction()
        if not last or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return None
        succs = sorted(allcc[-1].conditional_successors, key=lambda s: s.start_offset)
        if len(succs) != 2:
            return None
        t = next((s for s in succs if s.start_offset != last.argval), None)
        f = next((s for s in succs if s.start_offset == last.argval), None)
        if not (t and f):
            return None
        eff = [i for i in t.instructions if i.opname not in NOISE]
        if len(eff) == 1 and eff[0].opname == 'JUMP_FORWARD' and eff[0].argval is not None:
            t = analyzer.cfg.get_block_by_offset(eff[0].argval) or t
        if not (analyzer._is_single_expression_block(t)
                and analyzer._is_single_expression_block(f)):
            return None
        return (o(t), o(f))

    def patched(self, block, analyzer):
        r = orig(self, block, analyzer)
        if (not r) and self.chained_compare_blocks and block is self.entry \
                and self.entry is analyzer.cfg.entry_block \
                and getattr(self, 'chained_compare_ops', None) \
                and len(self.chained_compare_ops) >= 2:
            diamond = n3_predicate(self, block, analyzer)
            rec = {'code': analyzer._n3_code_name, 'block': o(block),
                   'cc_ops': list(self.chained_compare_ops),
                   'if_then': [o(b) for b in (self.then_blocks or [])],
                   'if_else': [o(b) for b in (self.else_blocks or [])],
                   'diamond': diamond,
                   'region_blocks': [o(b) for b in (self.blocks or [])]}
            hits.append(rec)
        return r

    IfRegion.can_be_ternary_header = patched
    fh = io.open(out, 'w', encoding='utf-8') if out else None
    for p in paths:
        root = load_pyc(p)
        if root is None:
            continue
        before = len(hits)
        for code in walk(root, []):
            try:
                cfg = build_cfg(code)
                an = RegionAnalyzer(cfg)
                an._n3_code_name = code.co_name
                an.analyze()
            except Exception:
                pass
        rel = p.replace('\\', '/')
        r0 = r'F:/Downloads/pythoncdc-main/site-packages/'
        if rel.startswith(r0):
            rel = rel[len(r0):]
        mine = hits[before:]
        rec = {'pyc': p, 'rel': rel, 'n': len(mine),
               'with_diamond': [h for h in mine if h['diamond']]}
        if fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fh.flush()
        if mine:
            print('%-58s candidates=%d diamond_ok=%d' % (rel[:58], len(mine),
                                                         len(rec['with_diamond'])))
            for h in mine[:8]:
                print('      %s blk@%s ops=%s then=%s else=%s diamond=%s' % (
                    h['code'], h['block'], h['cc_ops'], h['if_then'], h['if_else'], h['diamond']))
    IfRegion.can_be_ternary_header = orig
    if fh:
        fh.close()
    print('scan done: %d files, total R24-A CFG-entry vetoes=%d' % (len(paths), len(hits)))


if __name__ == '__main__':
    main()
