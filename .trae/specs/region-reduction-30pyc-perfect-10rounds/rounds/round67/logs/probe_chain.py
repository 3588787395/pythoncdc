# -*- coding: utf-8 -*-
"""probe_chain: print every BoolOp chain the LIVE analyzer builds for ONE function,
plus each member block's short-circuit jump target / fall-through, and the created
region's merge block.  Also reports which analyzer method produced it (python stack).

usage: python -X utf8 probe_chain.py <pyc> <funcname> [watch-offset ...]
"""
import io
import json
import marshal
import os
import sys
import traceback
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


def o(b):
    return getattr(b, 'start_offset', None)


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    watch = set(int(x) for x in sys.argv[3:])
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]

    from core.cfg import build_cfg
    import core.cfg.region_analyzer as A
    from core.cfg.region_analyzer import RegionAnalyzer

    _orig = RegionAnalyzer._create_boolop_region_from_chain

    def patched(self, chain, claimed):
        offs = [o(b) for b, _ in chain]
        if watch and not (set(offs) & watch):
            return _orig(self, chain, claimed)
        print('CHAIN %s ops=%s' % (offs, [op for _, op in chain]))
        for b, op in chain:
            last = b.get_last_instruction()
            succs = sorted(s.start_offset for s in b.conditional_successors)
            print('   blk@%-5s op=%-4s last=%-28s jt=%-5s succs=%s ninstr=%d' % (
                o(b), op, last.opname if last else None,
                last.argval if last else None, succs, len(b.instructions)))
        print('   callers: %s' % ' <- '.join(
            '%s:%s' % (os.path.basename(fr.filename), fr.lineno)
            for fr in traceback.extract_stack()[:-1][::-1]
            if 'probe_chain' not in fr.filename)[:400])
        r = _orig(self, chain, claimed)
        print('   -> region %s merge=%s blocks=%s' % (
            type(r).__name__ if r else None, o(getattr(r, 'merge_block', None)),
            [o(b) for b in (r.blocks if r else [])]))
        return r

    RegionAnalyzer._create_boolop_region_from_chain = patched

    cfg = build_cfg(code)
    an = RegionAnalyzer(cfg)
    regions = an.analyze()
    print()
    print('REGIONS %d' % len(regions))
    for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
        print('  %-18s entry=%-5s blocks=%s merge=%s then=%s else=%s' % (
            type(r).__name__, o(r.entry), [o(b) for b in (r.blocks or [])],
            o(getattr(r, 'merge_block', None)),
            [o(b) for b in (getattr(r, 'then_blocks', None) or [])],
            [o(b) for b in (getattr(r, 'else_blocks', None) or [])]))


if __name__ == '__main__':
    main()
