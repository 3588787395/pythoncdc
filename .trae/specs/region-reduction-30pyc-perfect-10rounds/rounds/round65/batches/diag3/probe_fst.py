# -*- coding: utf-8 -*-
"""probe_fst: instrument the landed generator's f-string-ternary path for ONE function.

usage: python -X utf8 probe_fst.py <pyc> <funcname>
Monkeypatches (in-memory only, no repo writes):
  RegionASTGenerator._try_wrap_fstring_pending_call
  RegionASTGenerator._ternary_pending_callee
  RegionASTGenerator._try_build_ternary_chained_container
  RegionASTGenerator._fstring_parts_from_segment
and prints every TernaryRegion's full structural attributes.
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'F:/Downloads/pythoncdc-main')

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator as G  # noqa: E402


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


def blofs(bs):
    return [o(x) for x in bs] if bs else bs


def dump_region(r):
    if not type(r).__name__.startswith('Ternary'):
        return
    print('TERNARY entry=%s blocks=%s merge=%s cond=%s ctx=%r container=%r dict_key=%r' % (
        o(r.entry), blofs(getattr(r, 'blocks', None)), o(getattr(r, 'merge_block', None)),
        o(getattr(r, 'condition_block', None)), getattr(r, 'merge_context', None),
        getattr(r, 'container_type', None), bool(getattr(r, 'dict_key_info', None))))
    for b in (r.blocks or []):
        eff = [i for i in b.instructions if i.opname not in ('CACHE',)]
        print('    blk@%-5s n=%d  %s' % (o(b), len(eff),
              ' '.join('%s@%s%s' % (i.opname, i.offset, ('(' + str(i.argval)[:12] + ')') if i.argval is not None else '') for i in eff)[:400]))


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]

    _wrap = G._try_wrap_fstring_pending_call
    _cal = G._ternary_pending_callee
    _chain = G._try_build_ternary_chained_container
    _seg = G._fstring_parts_from_segment

    def wrap(self, region, innermost_merge, joined_str):
        r = _wrap(self, region, innermost_merge, joined_str)
        print('  >> _try_wrap_fstring_pending_call(entry=%s, innermost_merge=%s) -> %s' % (
            o(region.entry), o(innermost_merge), 'HIT' if r else 'None'))
        return r

    def callee(self, cond_block):
        r = _cal(self, cond_block)
        print('     _ternary_pending_callee(blk@%s) -> %r' % (o(cond_block), r))
        return r

    def chain(self, region, ternary_expr):
        r = _chain(self, region, ternary_expr)
        print('  << _try_build_ternary_chained_container(entry=%s) -> %s' % (
            o(region.entry), (r or {}).get('type') if isinstance(r, dict) else r))
        return r

    def seg(self, segment, fv):
        r = _seg(self, segment, fv)
        print('     _fstring_parts_from_segment(nseg=%d) -> %s' % (len(segment), r))
        return r

    G._try_wrap_fstring_pending_call = wrap
    G._ternary_pending_callee = callee
    G._try_build_ternary_chained_container = chain
    G._fstring_parts_from_segment = seg

    cfg = build_cfg(code)
    g0 = G(cfg, top_level_code=code)
    regions = g0.region_analyzer.analyze()
    print('REGIONS=%d' % len(regions))
    for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
        dump_region(r)
    from core.cfg.region_ast_generator import generate_ast_from_regions
    print('--- GENERATE ---')
    ast = generate_ast_from_regions(cfg, top_level_code=code)
    print('--- done')
    import json
    txt = json.dumps(ast, ensure_ascii=False)
    print('AST len=%d' % len(txt))


if __name__ == '__main__':
    main()
