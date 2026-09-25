# -*- coding: utf-8 -*-
"""diag6 read-only probe: run the LIVE repo RegionASTGenerator on one function and
print the produced dict-AST tree (type/kind + a short payload digest).

usage: python -X utf8 probe_ast.py <pyc> <funcname> [--grep=SUBSTR] [--max=N]
"""
import io
import json
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


def name_of(node):
    if isinstance(node, dict):
        return node.get('type') or node.get('kind') or node.get('op') or node.get('name') or '?'
    return type(node).__name__


def digest(node):
    """short human digest of a dict node: names/consts/offset hints"""
    if not isinstance(node, dict):
        return repr(node)[:60]
    bits = []
    for k in ('func', 'value', 'test', 'target', 'name', 'id', 'operand'):
        v = node.get(k)
        if isinstance(v, dict):
            bits.append('%s=%s' % (k, name_of(v)))
        elif isinstance(v, (str, int, float, bool)) or v is None:
            if v is not None:
                bits.append('%s=%r' % (k, v))
    for k in ('targets', 'body', 'orelse', 'handlers', 'finalbody', 'stmts', 'value_list'):
        v = node.get(k)
        if isinstance(v, list):
            bits.append('%s=[%s]' % (k, ','.join(name_of(x) for x in v)))
    if 'names' in node and isinstance(node['names'], list):
        bits.append('names=%r' % ([getattr(x, 'id', x) if isinstance(x, dict) else x for x in node['names']][:4],))
    for k in ('offset', 'line', 'lineno'):
        if k in node:
            bits.append('%s=%s' % (k, node[k]))
    return ' '.join(str(b) for b in bits)[:150]


KEYS = ('type', 'kind', 'op', 'name', 'func', 'test', 'value', 'targets', 'body',
        'orelse', 'handlers', 'finalbody', 'stmts', 'elt', 'key', 'value_list',
        'operand', 'left', 'right', 'comparators', 'ops', 'args', 'keywords',
        'slice', 'target', 'id', 'attr', 'ctx', 'generators', 'pattern', 'cases',
        'items', 'variables', 'constants', 'names', 'offset', 'lineno', 'nested_blocks')


def pr(node, depth=0, out=None, path=''):
    pad = '  ' * depth
    if isinstance(node, dict):
        out.append('%s%s  {%s}' % (pad, name_of(node), digest(node)))
    elif isinstance(node, list):
        out.append('%s<list %d>' % (pad, len(node)))
    else:
        out.append('%s%r' % (pad, node))
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ('type', 'kind', 'op'):
                continue
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                out.append('%s.%s:' % (pad, k))
                for x in v:
                    pr(x, depth + 1, out, path + '/' + k)
            elif isinstance(v, dict):
                pr(v, depth + 1, out, path + '/' + k)
    elif isinstance(node, list):
        for x in node:
            pr(x, depth, out, path)


if __name__ == '__main__':
    kw = dict(x[2:].split('=', 1) for x in sys.argv[3:])
    pyc, fname = sys.argv[1], sys.argv[2]
    from core.cfg import build_cfg
    from core.cfg.region_ast_generator import RegionASTGenerator
    cs = [c for c in walk(load_pyc(pyc), []) if c.co_name == fname]
    for c in cs:
        cfg = build_cfg(c)
        gen = RegionASTGenerator(cfg, top_level_code=c if c.co_name == '<module>' else None)
        res = gen.generate()
        out = []
        pr(res, 0, out)
        txt = '\n'.join(out)
        g = kw.get('grep')
        if g:
            keep = []
            for i, l in enumerate(txt.splitlines()):
                if g in l:
                    keep.extend(txt.splitlines()[max(0, i - 6):i + 6])
                    keep.append('---')
            print('\n'.join(keep) or '(no match)')
        else:
            print(txt)
