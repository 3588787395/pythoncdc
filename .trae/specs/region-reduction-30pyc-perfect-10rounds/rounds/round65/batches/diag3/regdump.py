# -*- coding: utf-8 -*-
"""diag1 region dumper: run the LIVE repo analyzer on one function's code object and
print the region tree with the structural fields Round 63 cares about.

usage: python -X utf8 regdump.py <pyc> <funcname>
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


def o(b):
    return getattr(b, 'start_offset', None)


def L(bs):
    if bs is None:
        return None
    try:
        return sorted(o(x) for x in bs)
    except TypeError:
        return bs


FIELDS = ['entry', 'condition_block', 'header_block', 'merge_block', 'exit', 'then_blocks',
          'else_blocks', 'elif_conditions', 'body_blocks', 'cond_blocks', 'tail_block',
          'first_body_block', 'loop_exit_block', 'break_block', 'try_blocks', 'handler_blocks',
          'finalbody_blocks', 'orelse_blocks', 'value_block', 'then_block', 'else_block',
          'result_block', 'lhs_block', 'store_block']

DICTISH = ['chained_compare_blocks', 'chained_compare_ops', 'inline_boolop_chains',
           'boolop_chain', 'metadata', 'chained_comparison_blocks', 'chain_info']


def describe(r):
    parts = ['%s@%s' % (type(r).__name__, o(r.entry))]
    parts.append('blocks=%s' % (L(getattr(r, 'blocks', None))))
    for f in FIELDS:
        if hasattr(r, f):
            v = getattr(r, f)
            if v is None or (isinstance(v, (list, set, tuple)) and not v):
                continue
            if isinstance(v, (list, set, tuple)) and v and hasattr(v[0], 'start_offset'):
                parts.append('%s=%s' % (f, L(v)))
            elif isinstance(v, (bool, int, str)):
                parts.append('%s=%r' % (f, v))
    for f in DICTISH:
        if hasattr(r, f):
            v = getattr(r, f)
            if v:
                if f == 'metadata':
                    v = {k: val for k, val in v.items()
                         if k in ('is_loop_body', 'is_try', 'has_finally', 'is_generator_entry',
                                  'chained_compare', 'boolop_kind', 'ternary_kind', 'elif_chain')}
                    if not v:
                        continue
                s = repr(v)
                parts.append('%s=%s' % (f, s[:400]))
    parts.append('children=%s' % [ '%s@%s' % (type(c).__name__, o(c.entry)) for c in (r.children or [])])
    return ' '.join(parts)


def dump(code_obj, indent=0, seen=None):
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    cfg = build_cfg(code_obj)
    gen = RegionASTGenerator(cfg, top_level_code=code_obj if code_obj.co_name == '<module>' else None)
    regions = gen.region_analyzer.analyze()
    print('CFG %s: %d blocks, %d regions' % (code_obj.co_name, len(cfg.blocks), len(regions)))
    tops = [r for r in regions if getattr(r, 'parent', None) is None]
    print('TOP REGIONS (%d):' % len(tops))
    for r in sorted(tops, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
        print('  ' + describe(r))
    print()
    print('FULL TREE BY ENTRY:')
    for r in sorted(regions, key=lambda x: (o(x.entry) if o(x.entry) is not None else -1)):
        print('  ' + describe(r))
    return gen, regions


if __name__ == '__main__':
    pyc, name = sys.argv[1], sys.argv[2]
    cs = [c for c in walk(load_pyc(pyc), []) if c.co_name == name]
    if not cs:
        raise SystemExit('no code object named %s; have: %s' % (name, sorted({c.co_name for c in walk(load_pyc(pyc), [])})))
    for c in cs:
        dump(c)
