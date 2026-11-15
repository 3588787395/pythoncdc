#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r168 attribution tracer v2: callers + payloads for family E diagnostics.

usage: python -I -X utf8 probe168c.py <pyc> <code_name> [--lo=N --hi=N] [outfile]
"""
import marshal
import os
import sys
import traceback
import types

REPO = r"F:\Downloads\pythoncdc-main"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
os.chdir(REPO)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg import ast_generator_v2 as ag2

OUT = []


def P(*a):
    OUT.append(' '.join(str(x) for x in a))


def load_code(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def find_code(root, name):
    if root.co_name == name:
        return root
    for c in root.co_consts:
        if isinstance(c, types.CodeType):
            hit = find_code(c, name)
            if hit is not None:
                return hit
    return None


def offs(x):
    if hasattr(x, 'start_offset'):
        return x.start_offset
    if hasattr(x, 'entry') and hasattr(x.entry, 'start_offset'):
        return x.entry.start_offset
    return None


def types_of(r):
    if isinstance(r, list):
        return [n.get('type') if isinstance(n, dict) else type(n).__name__ for n in r]
    if isinstance(r, dict):
        return r.get('type')
    return type(r).__name__


def brief(node, depth=0):
    if isinstance(node, list):
        return '[' + ', '.join(brief(n, depth + 1) for n in node[:8]) + ']'
    if not isinstance(node, dict):
        return repr(node)[:40]
    t = node.get('type')
    if t == 'Name':
        return 'Name(%s)' % node.get('id')
    if t == 'Constant':
        return 'Const(%r)' % (node.get('value'),)
    if t == 'Attribute':
        return 'Attr(%s.%s)' % (brief(node.get('value')), node.get('attr'))
    if t == 'BoolOp':
        return 'BoolOp(%s, %s)' % (node.get('op'), brief(node.get('values'), depth))
    if t == 'Call':
        return 'Call(%s, args=%s)' % (brief(node.get('func')), brief(node.get('args'), depth))
    if t == 'Expr':
        return 'Expr(%s)' % brief(node.get('value'), depth)
    if t == 'Assign':
        return 'Assign(%s = %s)' % (brief(node.get('targets')), brief(node.get('value')))
    if t == 'If':
        return 'If(%s) body=%s' % (brief(node.get('test')), brief(node.get('body'), depth))
    if t == 'For':
        return 'For(%s) body=%s' % (brief(node.get('target')), brief(node.get('body'), depth))
    if t == 'FormattedValue':
        return 'Fmt(%s)' % brief(node.get('value'))
    if t == 'JoinedStr':
        return 'JoinedStr(%s)' % brief(node.get('values'))
    return t


def main():
    pyc, name = sys.argv[1], sys.argv[2]
    lo, hi, outfile = 0, 10 ** 9, None
    for a in sys.argv[3:]:
        if a.startswith('--lo='):
            lo = int(a.split('=', 1)[1])
        elif a.startswith('--hi='):
            hi = int(a.split('=', 1)[1])
        else:
            outfile = a

    def inwin(o):
        return o is not None and lo <= o <= hi

    def caller(skip=2):
        st = traceback.extract_stack()[:-skip]
        return ' <- '.join('%s:%d(%s)' % (os.path.basename(f.filename), f.lineno, f.name)
                           for f in st[-3:])

    code = find_code(load_code(pyc), name)
    cfg = build_cfg(code)

    METHODS = ['_generate_region', '_generate_block_statements',
               '_generate_block_statements_body', '_generate_if', '_if_generate_then_branch',
               '_generate_boolop', '_generate_ternary', '_loop_generate_for',
               '_process_if_blocks', '_build_boolop_expression',
               '_build_boolop_expression_inner', '_try_build_keeppop_target_grouped']

    for name_ in METHODS:
        orig = getattr(RegionASTGenerator, name_, None)
        if orig is None:
            P('!! missing method %s' % name_)
            continue

        def mk(orig=orig, name_=name_):
            def patched(self, *a, **kw):
                o = None
                for x in list(a) + list(kw.values()):
                    o2 = offs(x)
                    if o2 is not None:
                        o = o2
                        break
                r = orig(self, *a, **kw)
                if inwin(o):
                    ctx = ''
                    if a and hasattr(a[0], 'blocks'):
                        ctx = ' blocks=%s' % (sorted(b.start_offset for b in a[0].blocks)[:14],)
                        ctx += ' merge=%s' % (offs(getattr(a[0], 'merge_block', None)),)
                    P('%-36s @%-6s -> %s%s' % (name_, o, types_of(r), ctx))
                    P('     res=%s' % brief(r))
                    P('     from %s' % caller(3))
                return r
            return patched
        setattr(RegionASTGenerator, name_, mk())

    cls = ag2.ExpressionReconstructor
    orig_rec = cls.reconstruct

    def patched_rec(self, instructions, *a, **kw):
        r = orig_rec(self, instructions, *a, **kw)
        ops = [i.opname for i in instructions
               if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        o0 = instructions[0].offset if instructions else None
        if inwin(o0):
            P('  reconstruct @%s ops=%s -> %s' % (o0, ops, types_of(r)))
            P('      %s' % brief(r))
            P('      from %s' % caller(3))
        return r
    cls.reconstruct = patched_rec

    gen = RegionASTGenerator(cfg, top_level_code=None)
    ast = gen.generate()
    P('### body:')
    for st in ast.get('body', []):
        P('  ' + brief(st))
    text = '\n'.join(OUT)
    if outfile:
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write(text + '\n')
        print('wrote', outfile, len(OUT), 'lines')
    else:
        print(text)


if __name__ == '__main__':
    main()
