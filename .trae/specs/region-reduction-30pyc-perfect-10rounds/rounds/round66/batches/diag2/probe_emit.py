# -*- coding: utf-8 -*-
"""diag2 R66 probe: who emits a given statement, and how many times per region?

Read-only monkeypatch of the LANDED core (repo untouched; pycdc imported from
F:/Downloads/pythoncdc-main with sys.dont_write_bytecode=True).

usage: python -X utf8 probe_emit.py <pyc> <marker-substring> <out.txt>
"""
import io
import json
import os
import sys
import traceback
import types

REPO = r'F:\Downloads\pythoncdc-main'
sys.dont_write_bytecode = True
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

import pycdc  # noqa
import core.cfg.region_ast_generator as G  # noqa

PYC = sys.argv[1]
MARK = sys.argv[2]
OUT = sys.argv[3]

log = []


def compact(node, depth=0):
    if isinstance(node, dict):
        t = node.get('type')
        if t == 'Constant':
            return 'Constant(%r)' % (node.get('value'),)
        if t == 'Name':
            return 'Name(%s)' % node.get('id')
        if t == 'JoinedStr':
            return 'JoinedStr[%s]' % ','.join(compact(v, depth + 1)
                                             for v in node.get('values') or [])
        if t == 'FormattedValue':
            return 'FV(%s)' % compact(node.get('value'), depth + 1)
        if t == 'Call':
            return 'Call(%s)' % compact(node.get('func'), depth + 1)
        if t == 'Attribute':
            return 'Attr.%s' % node.get('attr')
        if t == 'Assign':
            return 'Assign(%s=%s)' % (','.join(compact(x) for x in node.get('targets') or []),
                                      compact(node.get('value'), depth + 1))
        if t == 'Return':
            return 'Return(%s)' % compact(node.get('value'), depth + 1)
        if t == 'Expr':
            return 'Expr(%s)' % compact(node.get('value'), depth + 1)
        return t or '?'
    return repr(node)


def stack_tail(limit=14):
    fr = traceback.extract_stack()[:-2]
    keep = [f for f in fr if 'region_ast_generator' in f.filename]
    return ' <- '.join('%s:%d' % (f.name, f.lineno) for f in keep[-limit:])


def region_desc(region):
    def st(b):
        try:
            return None if b is None else (b.start, [i.offset for i in b.instructions][:1],
                                           len(b.instructions))
        except Exception:
            return '?'
    return {
        'cls': type(region).__name__,
        'cond': st(getattr(region, 'condition_block', None)),
        'merge': st(getattr(region, 'merge_block', None)),
        'ctx': getattr(region, 'merge_context', None),
        'vt': str(getattr(region, 'value_target', None)),
        'nblk': len(getattr(region, 'blocks', []) or []),
        'blkstarts': [getattr(b, 'start', None) for b in (getattr(region, 'blocks', []) or [])],
    }


GT = G.RegionASTGenerator._generate_ternary
calls = {}


def gt(self, region, skip_store_targets=None):
    r = GT(self, region, skip_store_targets)
    rd = region_desc(region)
    key = (rd['cls'], rd['cond'], rd['merge'])
    calls[key] = calls.get(key, 0) + 1
    stmts = r if isinstance(r, list) else ([r] if r else [])
    txt = ' | '.join(compact(s) for s in stmts)
    if MARK and MARK in txt:
        log.append('CALL#%d %s  POST=%s\n   %s\n   %s'
                   % (calls[key], txt, [compact(x) for x in
                                        (getattr(region, 'post_consumer_extra_stmts', None) or [])],
                      json.dumps(rd), stack_tail()))
    return r


G.RegionASTGenerator._generate_ternary = gt

text = pycdc.decompile_pyc(PYC)
with io.open(OUT, 'w', encoding='utf-8') as fh:
    for i, l in enumerate(log):
        fh.write('[%d]\n%s\n' % (i, l))
    fh.write('\n=== region call counts ===\n')
    for k, v in calls.items():
        if v > 1:
            fh.write('x%d %s\n' % (v, json.dumps(k)))
    fh.write('\n=== product marker lines ===\n')
    for n, line in enumerate(text.split('\n'), 1):
        if MARK and MARK in line:
            fh.write('%d| %s\n' % (n, line))
print('log entries=%d' % len(log))
for i, l in enumerate(log[:8]):
    print('---', i)
    print(l)
