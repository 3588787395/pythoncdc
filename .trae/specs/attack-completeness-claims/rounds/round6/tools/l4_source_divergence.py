#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 语料外失败样本的**源码级**语义差异核对（§2 硬要求：不能只凭判据）。

对每个判据失败的 code object：
  1. 在**源码** AST 中按 qualname 路径定位同名函数/类；
  2. 在**产物** AST 中按同一路径定位；
  3. 比对两侧的「语义指纹」（语句类型多重集 / try / finally / except* / while /
     await / async with / match / return 数 / 关键常量 / 形参名 / 装饰器）；
  4. 输出可核对的差异条目（源位置 file:line ↔ 产物位置 file:line）。

用法：python -X utf8 l4_source_divergence.py [--only slug ...]
输出：logs/l4_source_divergence.json + logs/l4_source_divergence.md
"""
from __future__ import annotations

import argparse
import ast
import difflib
import glob
import json
import os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')
OFF = os.path.join(ROUND6, 'offcorpus')

# 指纹里关注的语义维度
DIM_KEYS = {
    'try': 'Try',
    'try_star': 'TryStar',
    'while': 'While',
    'for': 'For',
    'async_for': 'AsyncFor',
    'with': 'With',
    'async_with': 'AsyncWith',
    'match': 'Match',
    'await': 'Await',
    'async_func': 'AsyncFunctionDef',
    'yield': 'Yield',
    'break': 'Break',
    'continue': 'Continue',
    'return': 'Return',
    'raise': 'Raise',
    'assert': 'Assert',
    'global': 'Global',
    'nonlocal': 'Nonlocal',
    'lambda': 'Lambda',
    'comprehension': 'comprehension',
    'fstring': 'JoinedStr',
    'decorator': 'decorator',
    'delete': 'Delete',
    'augassign': 'AugAssign',
    'star_args': 'Starred',
    'namedexpr': 'NamedExpr',
    'slice': 'Slice',
    'ternary': 'IfExp',
    'boolop': 'BoolOp',
    'import': 'Import',
}


def qualname_map(tree: ast.Module):
    """qualname 路径 -> 节点（module 层无前缀）。"""
    out = {}

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = (prefix + '.' if prefix else '') + child.name
                out[q] = child
                walk(child, q + '.<locals>')
            elif isinstance(child, ast.ClassDef):
                q = (prefix + '.' if prefix else '') + child.name
                out[q] = child
                walk(child, q)
            else:
                walk(child, prefix)
    walk(tree, '')
    return out


def fingerprint(node) -> dict:
    """节点内（含嵌套）的语义指纹。"""
    counts = Counter()
    consts = []
    names = set()
    for n in ast.walk(node):
        t = type(n).__name__
        for k, v in DIM_KEYS.items():
            if t == v:
                counts[k] += 1
        if isinstance(n, ast.Constant):
            consts.append(repr(n.value))
        elif isinstance(n, ast.Name):
            names.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            counts['decorator'] += len(n.decorator_list)
            for d in n.decorator_list:
                counts['decorator'] += 0
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        counts['params'] = len(node.args.args) + len(node.args.kwonlyargs)
        counts['posonly'] = len(node.args.posonlyargs)
        counts['vararg'] = 1 if node.args.vararg else 0
        counts['kwarg'] = 1 if node.args.kwarg else 0
        counts['defaults'] = len(node.args.defaults)
        counts['decorators'] = len(node.decorator_list)
        counts['returns_ann'] = 1 if node.returns is not None else 0
        for a in list(node.args.args) + list(node.args.kwonlyargs) + list(node.args.posonlyargs):
            counts['ann_args'] += 1 if a.annotation is not None else 0
        counts['docstring'] = 1 if (node.body and isinstance(node.body[0], ast.Expr)
                                    and isinstance(node.body[0].value, ast.Constant)
                                    and isinstance(node.body[0].value.value, str)) else 0
    elif isinstance(node, ast.ClassDef):
        counts['decorators'] = len(node.decorator_list)
        counts['class_body_stmts'] = len(node.body)
    return {
        'counts': dict(counts),
        'consts': sorted(consts)[:40],
        'n_consts': len(consts),
        'n_names': len(names),
    }


def diff_fps(a: dict, b: dict):
    diffs = []
    keys = sorted(set(a['counts']) | set(b['counts']))
    for k in keys:
        va = a['counts'].get(k, 0)
        vb = b['counts'].get(k, 0)
        if va != vb:
            diffs.append('%s: 源=%d 产物=%d' % (k, va, vb))
    if a['n_consts'] != b['n_consts']:
        diffs.append('常量数: 源=%d 产物=%d' % (a['n_consts'], b['n_consts']))
    ca, cb = set(a['consts']), set(b['consts'])
    only_src = sorted(ca - cb)[:8]
    only_prod = sorted(cb - ca)[:8]
    if only_src:
        diffs.append('仅源常量: %s' % ', '.join(only_src))
    if only_prod:
        diffs.append('仅产物常量: %s' % ', '.join(only_prod))
    return diffs


def ast_diff(a_node, b_node, max_lines=14):
    """两侧 AST dump 的统一差分（可引用的结构级证据）。"""
    da = ast.dump(a_node, indent=1).splitlines()
    db = ast.dump(b_node, indent=1).splitlines()
    out = []
    for line in difflib.unified_diff(da, db, lineterm='', n=1):
        if line.startswith(('---', '+++', '@@')):
            continue
        s = line.strip()
        if s.startswith(('-', '+')):
            out.append(line.rstrip()[:220])
        if len(out) >= max_lines:
            out.append('...(截断)')
            break
    return out


def load_rows():
    rows = {}
    for p in sorted(glob.glob(os.path.join(LOGS, 'l4_diff_part*.json'))):
        for r in json.load(open(p, encoding='utf-8'))['rows']:
            rows[r['slug']] = r
    return [rows[k] for k in sorted(rows)]


def parse_fail_units(failures):
    out = []
    for f in failures or []:
        s = f.lstrip('*')
        if ':' in s:
            head = s.split(':', 1)[0]
        else:
            head = s
        head = head.replace('Failure detected at line number', '').strip()
        name = head.split(' ')[0]
        out.append(name)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*', default=None)
    args = ap.parse_args()

    rows = load_rows()
    if args.only:
        rows = [r for r in rows if r['slug'] in args.only]

    results = []
    md = ['# L4 语料外失败样本：源码级语义差异（§2 证据）', '',
          '> 判据读数见 `logs/l4_offcorpus_table.md`；本表是**源码级**核对，不依赖判据 verdict。',
          '> 「源=」指源码 AST 位置，「产物=」指 `offcorpus/<slug>OK.py` AST 位置。', '']
    for r in rows:
        slug = r['slug']
        v = r.get('verify', {})
        rec = {'slug': slug, 'status': v.get('status'), 'src': r.get('src'),
               'product': r.get('product'), 'units': []}
        if v.get('status') != 'failure':
            rec['note'] = '非 failure（compile_error / success）→ 不进入源码级差分'
            results.append(rec)
            continue
        src_path = r.get('src')
        prod_path = r.get('product')
        try:
            src_tree = ast.parse(open(src_path, encoding='utf-8', errors='replace').read())
        except Exception as exc:
            rec['note'] = '源码解析失败: %s' % exc
            results.append(rec)
            continue
        try:
            prod_tree = ast.parse(open(prod_path, encoding='utf-8', errors='replace').read())
        except Exception as exc:
            rec['note'] = '产物解析失败: %s' % exc
            results.append(rec)
            continue
        smap = qualname_map(src_tree)
        pmap = qualname_map(prod_tree)
        units = []
        for name in parse_fail_units(v.get('failures')):
            q = name[len('<module>'):].lstrip('.') if name.startswith('<module>') else name
            q = q.split('.Failure')[0]
            s_node = smap.get(q)
            p_node = pmap.get(q)
            entry = {'qualname': q,
                     'src_found': s_node is not None,
                     'prod_found': p_node is not None}
            if s_node is not None and p_node is not None:
                entry['src_line'] = s_node.lineno
                entry['prod_line'] = p_node.lineno
                entry['diffs'] = diff_fps(fingerprint(s_node), fingerprint(p_node))
                entry['ast_diff'] = ast_diff(s_node, p_node)
            elif s_node is not None:
                entry['src_line'] = s_node.lineno
                entry['note'] = '产物中**没有**同名定义（函数整体丢失）'
            else:
                entry['note'] = '源码中未按 qualname 定位到（可能是模块级或嵌套 code object）'
            units.append(entry)
        rec['units'] = units
        results.append(rec)
        md.append('## `%s`（判据 %s）' % (slug, v.get('status')))
        md.append('')
        md.append('- 源：`%s`' % src_path)
        md.append('- 产物：`%s`' % prod_path)
        if rec.get('note'):
            md.append('- 说明：%s' % rec['note'])
        md.append('')
        md.append('| 失败单元（qualname） | 源位置 | 产物位置 | 语义差异（源 vs 产物） |')
        md.append('|---|---|---|---|')
        for u in units:
            d = '；'.join(u.get('diffs', [])) if u.get('diffs') else (u.get('note') or '（指纹一致）')
            md.append('| `%s` | %s | %s | %s |' % (
                u['qualname'],
                ('L%s' % u['src_line']) if 'src_line' in u else '—',
                ('L%s' % u['prod_line']) if 'prod_line' in u else '—',
                d))
        md.append('')
        md.append('### AST 结构差分（源 vs 产物）')
        md.append('')
        for u in units:
            if not u.get('ast_diff'):
                continue
            md.append('**`%s`**（源 L%s ↔ 产物 L%s）' % (
                u['qualname'], u.get('src_line'), u.get('prod_line')))
            md.append('')
            md.append('```diff')
            for line in u['ast_diff']:
                md.append(line)
            md.append('```')
            md.append('')

    with open(os.path.join(LOGS, 'l4_source_divergence.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'results': results}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(LOGS, 'l4_source_divergence.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(md) + '\n')
    # 汇总：根因分类
    cats = Counter()
    for rec in results:
        for u in rec.get('units', []):
            for d in u.get('diffs', []):
                k = d.split(':')[0]
                if d.startswith('仅源常量') or d.startswith('仅产物常量'):
                    k = '常量集合差异'
                cats[k] += 1
            if u.get('note', '').startswith('产物中**没有**'):
                cats['函数整体丢失'] += 1
    print('[divergence] %d samples analysed' % len(results))
    for k, v in cats.most_common():
        print('  %-22s %d' % (k, v))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
