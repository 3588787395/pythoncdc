#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外失败单元的**字节码级**精确差分（§2 的证据来源）。

为什么需要它：
  * 判据（附件 `equivalence_check.py`）只给 verdict（Different bytecode / Different
    control flow），不给「差在哪」；
  * 源码 AST 指纹会把**语义等价**的差异也报出来（例：CPython 3.11 编译器把
    `"%s..." % (a, b)` 优化成 FORMAT_VALUE/BUILD_STRING，pycdc 还原成等价的
    f-string ⇒ 源码 AST 不同、字节码**相同**，不构成语义缺陷）；
  * 本脚本按 `co_qualname` 配对 code object，把指令流归一化后做序列差分，
    给出「原 pyc 有 / 产物没有（或多出 / 改写）」的精确指令级证据。

归一化规则：
  * 跳转指令的 argval 一律记为 `T`（偏移随布局变化）；
  * LOAD_CONST 的值记 `repr`（代码对象记 `<code:name>`）；
  * 其余按 (opname, argval) 比较。

输出：logs/l4_byte_diff.json（逐失败单元）
"""
from __future__ import annotations

import argparse
import difflib
import dis
import glob
import json
import marshal
import os
import py_compile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
OFF = os.path.join(ROUND6, 'offcorpus')


def load_pyc(path):
    with open(path, 'rb') as f:
        f.read(16)
        return marshal.load(f)


def code_tree(code):
    """co_qualname -> code object（同名多体按出现序配对）。"""
    out = {}

    def add(c):
        q = getattr(c, 'co_qualname', c.co_name)
        out.setdefault(q, []).append(c)
        for k in c.co_consts:
            if hasattr(k, 'co_code'):
                add(k)
    add(code)
    return out


def norm_instrs(code):
    out = []
    for ins in dis.get_instructions(code):
        op = ins.opname
        arg = ins.argval
        if ins.opcode in dis.hasjrel or ins.opcode in dis.hasjabs:
            arg = 'T'
        elif op == 'LOAD_CONST':
            if hasattr(arg, 'co_code'):
                arg = '<code:%s>' % arg.co_name
            else:
                arg = repr(arg)
        out.append('%s %s' % (op, arg))
    return out


def diff_seq(a, b, ctx=2, max_out=18):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        out.append('--- %s (orig[%d:%d] -> prod[%d:%d])' % (tag, i1, i2, j1, j2))
        for x in a[i1:i2][:6]:
            out.append('  - ' + x[:150])
        if i2 - i1 > 6:
            out.append('  - ...(%d more)' % (i2 - i1 - 6))
        for x in b[j1:j2][:6]:
            out.append('  + ' + x[:150])
        if j2 - j1 > 6:
            out.append('  + ...(%d more)' % (j2 - j1 - 6))
        if len(out) >= max_out:
            out.append('  ...(截断)')
            break
    return out


def parse_fail_units(failures):
    out = []
    for f in failures or []:
        s = f.lstrip('*')
        head = s.split(':', 1)[0]
        name = head.split(' ')[0]
        if name.startswith('<module>') and len(name) > len('<module>'):
            name = name[len('<module>'):].lstrip('.')
        out.append(name)
    return out


def load_rows():
    rows = {}
    for p in sorted(glob.glob(os.path.join(LOGS, 'l4_diff_part*.json'))):
        for r in json.load(open(p, encoding='utf-8'))['rows']:
            rows[r['slug']] = r
    return [rows[k] for k in sorted(rows)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=None)
    ap.add_argument('--max-units', type=int, default=6, help='每样本最多分析多少失败单元')
    args = ap.parse_args()

    rows = load_rows()
    if args.only:
        rows = [r for r in rows if r['slug'] in args.only]

    results = []
    for r in rows:
        v = r.get('verify', {})
        rec = {'slug': r['slug'], 'status': v.get('status'), 'units': []}
        if v.get('status') != 'failure':
            results.append(rec)
            continue
        try:
            orig = load_pyc(r['pyc_copy'])
            with tempfile.TemporaryDirectory() as td:
                cpath = os.path.join(td, 'p.pyc')
                py_compile.compile(r['product'], cfile=cpath, doraise=True, optimize=0)
                prod = load_pyc(cpath)
        except Exception as exc:
            rec['error'] = '%s: %s' % (type(exc).__name__, exc)
            results.append(rec)
            continue
        omap, pmap = code_tree(orig), code_tree(prod)
        units = []
        for q in parse_fail_units(v.get('failures')):
            if len(units) >= args.max_units:
                break
            ol, pl = omap.get(q, []), pmap.get(q, [])
            if not ol or not pl:
                units.append({'qualname': q, 'note': '配对失败（原=%d 产物=%d）' % (len(ol), len(pl))})
                continue
            a = norm_instrs(ol[0])
            b = norm_instrs(pl[0])
            d = diff_seq(a, b)
            units.append({'qualname': q,
                          'n_orig_instr': len(a), 'n_prod_instr': len(b),
                          'bytecode_equal': a == b,
                          'diff': d})
        rec['units'] = units
        results.append(rec)
        ndiff = sum(1 for u in units if u.get('diff'))
        print('[byte-diff] %-28s units=%d 有指令级差异=%d' % (r['slug'], len(units), ndiff))

    with open(os.path.join(LOGS, 'l4_byte_diff.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'results': results}, f, ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
