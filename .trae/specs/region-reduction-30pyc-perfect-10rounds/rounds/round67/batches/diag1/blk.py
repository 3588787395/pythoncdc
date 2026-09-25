# -*- coding: utf-8 -*-
"""diag1 r67: per-block CFG + region dump for ONE function, landed bytes (read-only).

usage: python -X utf8 blk.py <pyc> <func>
"""
import io
import marshal
import os
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')


def load_pyc(path):
    data = io.open(path, 'rb').read()
    for off in (16, 12, 8):
        try:
            return marshal.loads(data[off:])
        except Exception:
            continue
    raise SystemExit('cannot unmarshal')


def walk(code, out):
    out.append(code)
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            walk(c, out)
    return out


def tail_op(b):
    import dis
    ins = [i for i in dis.get_instructions(b.code_obj) if i.opname != 'CACHE'] if hasattr(b, 'code_obj') else []
    return ins[-1].opname if ins else getattr(b, 'last_opname', getattr(b, 'terminator', None))


def off(b):
    """REAL bytecode offset of a block (its first instruction)."""
    try:
        i = b.get_first_instruction()
        if i is not None:
            return i.offset
    except Exception:
        pass
    ins = getattr(b, 'instructions', None) or []
    return ins[0].offset if ins else getattr(b, 'start_offset', None)


def _key(b):
    v = off(b)
    return -1 if v is None else v


def main(pyc, name):
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    cs = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    assert len(cs) == 1, len(cs)
    co = cs[0]
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    regs = gen.region_analyzer.analyze()
    raw = cfg.blocks
    bl = sorted(list(raw.values()) if isinstance(raw, dict) else list(raw), key=_key)
    print('== BLOCKS %s (%d) ==' % (name, len(bl)))
    for b in bl:
        succ = [off(s) if hasattr(s, 'instructions') else s for s in (b.successors or [])]
        pred = [off(s) if hasattr(s, 'instructions') else s for s in (b.predecessors or [])]
        n = len(getattr(b, 'instructions', []) or [])
        print(' blk@%-5s id=%-4s n=%-3d term=%-26s succ=%-22s pred=%s'
              % (off(b), getattr(b, 'id', '?'), n,
                 str(getattr(b, 'terminator', getattr(b, 'last_op', ''))), succ, pred))

    print('== REGIONS (%d) ==' % len(regs))

    def o(r):
        return off(r.entry)
    for r in sorted(regs, key=lambda x: (o(x) if o(x) is not None else -1)):
        par = getattr(r, 'parent', None)
        bs = sorted(off(b) for b in (getattr(r, 'blocks', None) or []))
        print(' %-26s entry@%-5s blocks=%s parent=%s' % (
            type(r).__name__, o(r), bs,
            ('%s@%d' % (type(par).__name__, o(par))) if par is not None else None))
        for f in ('condition_block', 'then_block', 'else_block', 'merge_block', 'exit',
                  'header_block', 'tail_block', 'first_body_block', 'loop_exit_block'):
            v = getattr(r, f, None)
            if v is not None and hasattr(v, 'instructions'):
                print('        %-16s @%s' % (f, off(v)))
            elif isinstance(v, (list, tuple)) and v and hasattr(v[0], 'instructions'):
                print('        %-16s %s' % (f, [off(x) for x in v]))

        ch = getattr(r, 'children', None) or []
        if ch:
            print('        children: %s' % ['%s@%s' % (type(c).__name__, o(c)) for c in ch])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
