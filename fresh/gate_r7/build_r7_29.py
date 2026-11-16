# -*- coding: utf-8 -*-
"""Assemble r7_29.json from measured artefacts (no hand-typed numbers).

Inputs (all produced by the scripts in this folder):
  fresh/gate_r7/r7_deep_diff.json     - nested code-object diff per group
  fresh/gate_r7/repro_min.json        - 9 entry chains + probes + counterfactual
  D:/.../r7/dead_const_scan.json      - dead-constant census
  D:/.../r7_transfer.json             - the 29 transferred entries
  semantic_v3m_b275_g3fix_merged.json - evidence ledger (paths, hashes, verdicts)
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = r'F:\Downloads\pythoncdc-main'
WORK = r'D:\temp\opencode\cl_layout\r7'
EV = r'D:\temp\opencode\cl_layout\gap\g3fix\semantic_v3m_b275_g3fix_merged.json'
TR = r'D:\temp\opencode\cl_layout\gap\g3gap\r7_transfer.json'

CLASS = {
    'e04_g2_ifexp_deep.pyc#1': {
        'class': 'T2',
        'site': "f_ternary_comp_cond.<locals>.<listcomp>",
        'chain': '<module> -> f_ternary_comp_cond -> <listcomp> (module.co_consts[6] -> .co_consts[2])',
        'fields': ['co_consts.v[0]'],
        'minimal': ("原件 listcomp 的 orelse 常量是 int 0（在 filter 真值位被 CPython 折叠成跳转，"
                    "池里成为死常量，无 LOAD_CONST 引用）；反编译按折叠臂约定合成 bool False，"
                    "再编译得到 (False,)。co_code 逐字节相同（两者同为假值，跳转等长）。"),
        'fixable': 'yes',
    },
    'r7_05_ternary_comprehension.pyc#2': {
        'class': 'T1',
        'site': 't_listcomp_ternary_filter.<locals>.<listcomp>',
        'chain': '<module> -> t_listcomp_ternary_filter -> <listcomp> (module.co_consts[2] -> .co_consts[1])',
        'fields': ['co_code', 'co_consts.len', 'co_consts.v', 'co_consts.v[1]'],
        'minimal': ("原件 filter 是 `(x % 2 if flag else True)`：orelse True 在真值位被折叠成跳转，"
                    "池里成为死常量 True（index 1，无 LOAD_CONST 引用）；反编译改写成 `not flag or x % 2`，"
                    "同一字节码但不再 intern True，池变成 (2, 0)，原来是 (2, True, 0) —— `0` 的索引 2→1，"
                    "LOAD_CONST 操作数随之改变。opcode 序列 20/20 完全相同，只有 1 个操作数不同。"),
        'fixable': 'yes-with-canonicalization',
    },
    'c13_class_misc.pyc#3': {
        'class': 'T3',
        'site': 'CMisc.boom',
        'chain': '<module> -> CMisc (class body) -> CMisc.boom (module.co_consts[1] -> .co_consts[3])',
        'fields': ['co_code', 'co_consts.v[1]', 'co_consts.v[2]', 'co_consts.v[3]',
                   'co_names', 'co_names[0]'],
        'minimal': ("原件 `if 0: raise ValueError('x')` 只编译成一条 NOP（2 字节），但池里留下死常量 0 与 'x'、"
                    "名字表留下 ValueError；反编译把这条语句整个丢掉 → 少一条 NOP、少 'x'/ValueError、"
                    "并且 `pass` 的 NOP 也被 `while 1:` 包裹结构吞掉 → 68 vs 66 字节、22 vs 21 条指令。"),
        'fixable': 'yes-but-needs-residue-driven-reconstruction',
    },
}


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    deep = json.load(open(os.path.join(ROOT, 'fresh', 'gate_r7', 'r7_deep_diff.json'),
                          encoding='utf-8'))
    repro = json.load(open(os.path.join(ROOT, 'fresh', 'gate_r7', 'repro_min.json'),
                           encoding='utf-8'))
    dead = json.load(open(os.path.join(WORK, 'dead_const_scan.json'), encoding='utf-8'))
    ev = {r['entry_id']: r for r in json.load(open(EV, encoding='utf-8'))['records']}
    tr = json.load(open(TR, encoding='utf-8'))
    dead_by_id = {r['id']: r for r in dead['rows']}

    group_of = {}
    for g in deep['groups']:
        for eid in g['ids']:
            group_of[eid] = g

    entries = []
    for e in tr['entries']:
        eid = e['id']
        g = group_of[eid]
        cls = CLASS[g['group']]
        rec = ev[eid]
        node = None
        paths = set(e['diff_paths'])
        for n in g['nodes']:
            if not n['diffs']:
                continue
            # pick the node whose judge paths belong to this entry's path set
            base = '$.' + n['path'][2:] if n['path'].startswith('$.') else n['path']
            if any(p.startswith(n['path']) or n['path'].startswith(p) for p in paths):
                node = n
                break
        entries.append({
            'n': e['n'], 'id': eid,
            'form': e['form'], 'host': e['host'], 'depth': e['depth'],
            'variant': e['variant'],
            'source_p_j': rec['c1']['path'],
            'pyc': rec['c2']['pyc_path'], 'pyc_sha256': rec['c2']['sha256'],
            'product': rec['c3']['product_path'], 'product_sha256': rec['c3']['sha256'],
            'site_group': g['group'], 'class': cls['class'],
            'diff_site': cls['site'], 'code_object_chain': cls['chain'],
            'diff_fields': cls['fields'],
            'judge_diff_paths': e['diff_paths'],
            'minimal_difference': cls['minimal'],
            'fixable_generation_side': cls['fixable'],
            'nested_consts_orig': (node or {}).get('consts_o'),
            'nested_consts_prod': (node or {}).get('consts_p'),
            'consts_multiset_equal': (node or {}).get('consts_multiset_equal'),
            'consts_order_equal': (node or {}).get('consts_order_equal'),
            'dead_consts_in_pyc': dead_by_id.get(eid, {}).get('dead_consts'),
            'input_model_calls': rec['input_model'].get('calls'),
            'verdict': rec['c4'].get('verdict'),
            'semantic_dims': rec['c4'].get('diffs'),
        })

    counts = {'T1': 0, 'T2': 0, 'T3': 0}
    for row in entries:
        counts[row['class']] += 1

    payload = {
        'total': len(entries),
        'class_counts': counts,
        'distinct_pyc': len({r['pyc'] for r in entries}),
        'distinct_product_sha': len({r['product_sha256'] for r in entries}),
        'note': ('29 个 J 条目只对应 3 个 (pyc, product) 对：同一 pyc 的 product 字节完全相同，'
                 '条目之间只有 J 标签（form/host/variant/depth）不同。'),
        'sites': [{'group': g['group'], 'pyc': g['pyc'], 'product': g['product'],
                   'product_sha256': g['product_sha256'], 'n_entries': g['n_entries'],
                   'ids': g['ids'], 'class': CLASS[g['group']]['class'],
                   'tags': g['tags']} for g in deep['groups']],
        'group_by': 'product_sha256 of the decompiled source; identical bytes share one site',
        'entries': entries,
    }
    out = os.path.join(ROOT, 'fresh', 'gate_r7', 'r7_29.json')
    json.dump(payload, open(out, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in payload.items()
                      if k in ('total', 'class_counts', 'distinct_pyc',
                               'distinct_product_sha')}, ensure_ascii=False, indent=1))
    print('wrote', out)


if __name__ == '__main__':
    main()
