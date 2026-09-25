# -*- coding: utf-8 -*-
"""diag1 runtime tracer: monkeypatch RegionASTGenerator methods and log what fires
for a chosen set of block offsets (entry offsets) inside ONE function.

usage: python -X utf8 trace.py <pyc> <funcname> <comma-sep offsets> [--full]
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
    raise SystemExit('cannot unmarshal %s' % path)


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def stype(s):
    if not isinstance(s, dict):
        return repr(s)[:40]
    t = s.get('type')
    if t == 'Assign':
        tg = s.get('targets') or [{}]
        return 'Assign(%s)' % (tg[0].get('id') or tg[0].get('attr') or tg[0].get('slice', {}).get('value', {}).get('id') or '?')
    if t == 'Expr':
        return 'Expr(%s)' % (s.get('value') or {}).get('type')
    if t == 'If':
        return 'If(n=%d,e=%d)' % (len(s.get('body') or []), len(s.get('orelse') or []))
    if t == 'Return':
        return 'Return(%s)' % (s.get('value') or {}).get('type')
    return t or '?'


def main():
    pyc, name, offs = sys.argv[1], sys.argv[2], sys.argv[3]
    WATCH = set(int(x) for x in offs.replace(',', ' ').split())
    codes = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(codes) == 1, [c.co_firstlineno for c in codes]
    code = codes[0]

    from core.cfg import build_cfg
    import core.cfg.region_ast_generator as G
    from core.cfg.region_ast_generator import RegionASTGenerator, BoolOpRegion, IfRegion

    hits = []

    def o(b):
        return getattr(b, 'start_offset', None)

    def L(bs):
        return sorted(x for x in (o(b) for b in (bs or [])) if x is not None)

    def desc(r):
        return '%s@%s blocks=%s merge=%s entry=%s parent=%s' % (
            type(r).__name__, o(r.entry), L(getattr(r, 'blocks', None)),
            o(getattr(r, 'merge_block', None)), o(r.entry),
            (type(r.parent).__name__ + '@' + str(o(r.parent.entry))) if getattr(r, 'parent', None) else None)

    _orig_gen_region = RegionASTGenerator._generate_region
    _orig_downstream = RegionASTGenerator._downstream_region_entry
    _orig_gen_boolop = RegionASTGenerator._generate_boolop
    _orig_gen_boolop_impl = RegionASTGenerator._generate_boolop_impl
    _orig_build_boolop_expr = RegionASTGenerator._build_boolop_expression
    _orig_if_gen = getattr(RegionASTGenerator, '_if_generate_normal', None)

    DEPTH = [0]

    def _generate_region(self, region, *a, **k):
        want = o(region.entry) in WATCH or (set(L(getattr(region, 'blocks', None))) & WATCH)
        if want:
            print('%s> _generate_region %s skip_store_targets=%s' % ('  ' * DEPTH[0], desc(region), a))
        DEPTH[0] += 1
        r = _orig_gen_region(self, region, *a, **k)
        DEPTH[0] -= 1
        if want:
            print('%s< _generate_region -> %s' % ('  ' * DEPTH[0],
                  [stype(x) for x in r] if isinstance(r, list) else stype(r) if r else r))
        return r

    def _downstream(self, block, exclude):
        r = _orig_downstream(self, block, exclude)
        if o(block) in WATCH:
            print('%s> _downstream_region_entry(block=%s, exclude=%s) -> %s' % (
                '  ' * DEPTH[0], o(block), desc(exclude) if exclude is not None else None,
                desc(r) if r is not None else None))
        return r

    def _gen_boolop(self, region, *a, **k):
        want = o(region.entry) in WATCH or (set(L(getattr(region, 'blocks', None))) & WATCH)
        if want:
            print('%s> _generate_boolop %s value_target=%r op_chain=%s prefix_block=%s' % (
                '  ' * DEPTH[0], desc(region), getattr(region, 'value_target', None),
                [(o(b), op) for b, op in (region.op_chain or [])], o(getattr(region, 'prefix_block', None))))
        DEPTH[0] += 1
        r = _orig_gen_boolop(self, region, *a, **k)
        DEPTH[0] -= 1
        if want:
            print('%s< _generate_boolop -> %s' % ('  ' * DEPTH[0],
                  [stype(x) for x in r] if isinstance(r, list) else stype(r) if r else r))
        return r

    def _build_boolop_expr(self, region, *a, **k):
        r = _orig_build_boolop_expr(self, region, *a, **k)
        if o(region.entry) in WATCH:
            print('%s. _build_boolop_expression(%s) -> %s' % ('  ' * DEPTH[0], desc(region),
                  repr(r)[:160]))
        return r

    RegionASTGenerator._generate_region = _generate_region
    RegionASTGenerator._downstream_region_entry = _downstream
    RegionASTGenerator._generate_boolop = _gen_boolop
    RegionASTGenerator._build_boolop_expression = _build_boolop_expr

    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg)
    gen._diag_watch = WATCH
    ast = gen.generate()
    print()
    print('==== GENERATED BLOCKS around watch ====')
    for b in sorted([x for x in cfg.blocks if hasattr(x, 'start_offset')], key=lambda x: x.start_offset):
        if b.start_offset in WATCH:
            reg = gen.region_analyzer.block_to_region.get(b)
            print(' blk@%-6s n=%-3d generated=%-5s owner=%s' % (
                b.start_offset, len(b.instructions), b in gen.generated_blocks,
                desc(reg) if reg else None))
    print()
    import json
    print('==== AST DUMP ====')
    print(json.dumps(ast, ensure_ascii=False)[:200])


if __name__ == '__main__':
    main()
