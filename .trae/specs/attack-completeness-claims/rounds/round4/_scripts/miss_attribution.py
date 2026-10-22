#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L2 判定层攻击：**漏检归因器**（把每一次「判据判绿但语义已错」归到四类）。

四类归因（逐级判定）：
  L0-RAW      两侧**归一化前**的指令流（opname/opcode/optype/real_size/has_arg/
              has_extended_arg/offset/is_jump_target/argval 原样）就相同
              ⇒ 差异**根本不在指令流里**（落在 co_consts / co_varnames / co_flags /
                co_names / co_freevars 等判据**从不比较**的维度）⇒ OUT-OF-INSTRUCTION
  L1-NORM     经判据 patch 链（remove_extended_arg, remove_nop, fix_indirect_jump,
              fix_unreachable, remove_extended_arg, replace_firstlno）后，
              **按判据自身的比较语义**（argval 用 Python `==`）仍相同
              ⇒ 差异被**归一化抹平** ⇒ NORMALIZED-AWAY
  L2-TYPE     同上但 argval 用**类型敏感**标签（1 / True / 1.0 可分辨）后不同
              ⇒ 差异**判据看得见**却仍判绿 ⇒ 比较算子可改进（`==` 抹平类型）⇒ COMPARATOR-BLIND
  L3-DIFF     前述都不成立 ⇒ 判据应判红（若此处仍判绿，则是判据管线本身的缺陷）

用法：
  python -X utf8 miss_attribution.py [--jsonl <mutation_results.jsonl>] [--json out.json]
                                     [--keep <dir>]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND4 = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(ROUND4, '..', '..', '..', '..', '..'))
OUT = os.path.join(ROUND4, '_out')

DEFAULT_PYLINGUAL = r'D:\Desktop\ptrade相关\pylingual'


def load_pyc(root=DEFAULT_PYLINGUAL):
    root = os.path.abspath(root)
    sys.path.insert(0, root)
    import typing
    if not hasattr(typing, 'override'):
        typing.override = lambda f: f
    if 'pydot' not in sys.modules:
        stub = types.ModuleType('pydot')
        stub.graph_from_dot_data = lambda *a, **k: []
        stub.Dot = stub.Node = stub.Edge = lambda *a, **k: None
        sys.modules['pydot'] = stub
    if 'pylingual' not in sys.modules:
        pkg = types.ModuleType('pylingual')
        pkg.__path__ = [os.path.join(root, 'pylingual')]
        sys.modules['pylingual'] = pkg
    from pylingual.editable_bytecode import PYCFile
    from pylingual.editable_bytecode.bytecode_patches import (
        fix_indirect_jump, fix_unreachable, remove_extended_arg, remove_nop, replace_firstlno)
    patches = [remove_extended_arg, remove_nop, fix_indirect_jump,
               fix_unreachable, remove_extended_arg, replace_firstlno]
    return PYCFile, patches


def tag(v):
    if isinstance(v, bool):
        return ('bool', v)
    if isinstance(v, int):
        return ('int', v)
    if isinstance(v, float):
        return ('float', repr(v))
    if isinstance(v, complex):
        return ('complex', repr(v))
    if isinstance(v, str):
        return ('str', v)
    if isinstance(v, bytes):
        return ('bytes', v)
    if v is None:
        return ('none',)
    if isinstance(v, tuple):
        return ('tuple', tuple(tag(x) for x in v))
    if isinstance(v, frozenset):
        return ('frozenset', tuple(sorted(repr(tag(x)) for x in v)))
    return (type(v).__name__, repr(v))


JUDGE_FIELDS = ('opname', 'opcode', 'optype', 'real_size', 'has_arg',
                'has_extended_arg', 'offset', 'is_jump_target')


def fingerprint(pyc_path, PYCFile, patches, apply_patches, mode):
    """mode:
      'judge' ⇒ 判据**实际比较**的字段集合，argval 保持原值（Python `==` 语义，
                `1 == True` ⇒ 不可分辨）
      'type' ⇒ 同 'judge'，但 LOAD_CONST 的 argval 换成类型敏感标签
      'full' ⇒ 'judge' 字段 + **arg（槽位下标）** + argval 的 repr（任何差异可见）
    """
    f = PYCFile(pyc_path)
    if apply_patches:
        f.apply_patches(list(patches))
    out = []
    for bc in f.iter_bytecodes():
        items = []
        for i in bc:
            av = i.argval
            if isinstance(av, types.CodeType):
                av = ('code', av.co_name)
            elif mode == 'type' and i.opname == 'LOAD_CONST':
                av = tag(av)
            elif mode == 'full':
                av = repr(av)
            row = tuple(getattr(i, k, None) for k in JUDGE_FIELDS) + (av,)
            if mode == 'full':
                row = row + (getattr(i, 'arg', None),)
            items.append(row)
        out.append((bc.name, items))
    out.sort(key=lambda r: (r[0], repr(r[1])))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jsonl', default=os.path.join(OUT, 'mutation_results.jsonl'))
    ap.add_argument('--json', default=os.path.join(OUT, 'miss_attribution.json'))
    ap.add_argument('--keep', default=os.path.join(ROUND4, '_probes', 'miss'))
    args = ap.parse_args()

    PYCFile, patches = load_pyc()
    import py_compile
    import tempfile
    tmp = tempfile.mkdtemp(prefix='missattr_')

    rows = []
    seen = set()
    for line in open(args.jsonl, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        key = (r['pyc'], r['family'])
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)
    base = {r['pyc']: r for r in rows if r['family'] == 'BASELINE'}
    green = {p for p, r in base.items() if r['status'] == 'success'}

    if args.keep:
        os.makedirs(args.keep, exist_ok=True)

    miss_rows = [r for r in rows
                 if r['family'] != 'BASELINE' and r['pyc'] in green
                 and r['status'] == 'success']
    print('miss rows to attribute: %d' % len(miss_rows))

    out_rows = []
    stat = collections.defaultdict(collections.Counter)
    for r in miss_rows:
        prod = r['pyc'][:-4] + 'OK.py'
        if not os.path.isfile(prod):
            r2 = dict(r, attribution='NO_PRODUCT')
            out_rows.append(r2)
            stat[r['family']]['NO_PRODUCT'] += 1
            continue
        raw = open(prod, 'rb').read()
        sys.path.insert(0, HERE)
        import mutation_lib
        mut, site = mutation_lib.apply_mutation(r['family'], raw)
        if mut is None:
            r2 = dict(r, attribution='NOT_REPRODUCIBLE')
            out_rows.append(r2)
            stat[r['family']]['NOT_REPRODUCIBLE'] += 1
            continue
        mpy = os.path.join(tmp, 'm.py')
        open(mpy, 'wb').write(mut)
        mpyc = os.path.join(tmp, 'm.pyc')
        py_compile.compile(mpy, cfile=mpyc, doraise=True, optimize=0)
        def fp(path, mode, apply_patches=True):
            return fingerprint(path, PYCFile, patches, apply_patches, mode)

        norm_judge, norm_judge_b = fp(r['pyc'], 'judge'), fp(mpyc, 'judge')
        if norm_judge != norm_judge_b:
            attr = 'PIPELINE-DEFECT'
            same = dict(judge_same=False, typesens_same=None, full_same=None, raw_same=None)
        else:
            norm_type, norm_type_b = fp(r['pyc'], 'type'), fp(mpyc, 'type')
            if norm_type != norm_type_b:
                attr = 'COMPARATOR-BLIND'
                same = dict(judge_same=True, typesens_same=False, full_same=None, raw_same=None)
            else:
                norm_full, norm_full_b = fp(r['pyc'], 'full'), fp(mpyc, 'full')
                if norm_full != norm_full_b:
                    attr = 'SLOT-INDEX-BLIND'
                    same = dict(judge_same=True, typesens_same=True, full_same=False, raw_same=None)
                else:
                    raw_full, raw_full_b = fp(r['pyc'], 'full', False), fp(mpyc, 'full', False)
                    if raw_full != raw_full_b:
                        attr = 'NORMALIZED-AWAY'
                        same = dict(judge_same=True, typesens_same=True, full_same=True, raw_same=False)
                    else:
                        attr = 'OUT-OF-INSTRUCTION'
                        same = dict(judge_same=True, typesens_same=True, full_same=True, raw_same=True)
        stat[r['family']][attr] += 1
        rec = dict(r, attribution=attr, site=site, **same)
        out_rows.append(rec)
        if args.keep:
            import hashlib
            d = hashlib.md5(('%s|%s' % (r['pyc'], r['family'])).encode('utf-8')).hexdigest()[:16]
            dst = os.path.join(args.keep, 'miss_%s_%s.py' % (d, r['family']))
            open(dst, 'wb').write(mut)
            rec['kept'] = os.path.relpath(dst, ROOT).replace('\\', '/')

    with open(args.json, 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'attribution': {k: dict(v) for k, v in stat.items()},
                   'rows': out_rows}, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print()
    for fam in sorted(stat):
        print('%-20s %s' % (fam, dict(stat[fam])))
    print('-> %s' % args.json)


if __name__ == '__main__':
    sys.exit(main())
