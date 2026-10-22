#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L4 / Task 6 — 失败样本的**根因分类**（§2 表的「语义差异」列）。

输入：logs/l4_byte_diff.json（指令级差分）+ logs/l4_source_divergence.json（AST 指纹）。
输出：logs/l4_classify.json + logs/l4_classify.md

分类规则（按优先级，先命中先算）：
  C1 局部变量写入丢失/改写   : 差分出现 STORE_FAST→STORE_ATTR/LOAD_GLOBAL，或 STORE_FAST 消失而同名 LOAD_GLOBAL 出现
  C2 语句/校验被删除         : 差分出现整块 delete（含 LOAD_CONST '...' + RAISE / CALL / POP_TOP）
  C3 分支极性反转             : JUMP_IF_TRUE_OR_POP ↔ JUMP_IF_FALSE_OR_POP 互换
  C4 返回值丢失               : RETURN_VALUE / Return 节点减少或函数体以 None 返回
  C5 await/异步路径丢失       : AWAIT 指令减少
  C6 注解/形参槽位丢失        : 注解节点减少（ann_args / returns_ann）
  C7 类成员/属性丢失          : 类体语句减少 / STORE_ATTR 目标减少
  C8 条件赋值丢失(未绑定)     : 赋值目标 STORE_FAST 减少而读取仍在
  C9 切片/下标丢失            : BUILD_SLICE / 切片节点减少
  C10 try/except/else 塌陷    : 差分中出现 handler 或 else 分支丢失
  C11 等价改写（不构成语义差）: 差分仅为 `%`-格式化→f-string、常量顺序、LOAD_CONST 增删而控制流不变
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND6 = os.path.dirname(HERE)
LOGS = os.path.join(ROUND6, 'logs')

RULES = [
    ('C1', '局部变量写入丢失/改写为属性',
     [re.compile(r'STORE_FAST (\w+)'), re.compile(r'LOAD_GLOBAL (\w+)'), re.compile(r'STORE_ATTR')]),
    ('C3', '分支极性反转',
     [re.compile(r'JUMP_IF_TRUE_OR_POP'), re.compile(r'JUMP_IF_FALSE_OR_POP')]),
    ('C5', 'await/异步路径丢失', [re.compile(r'AWAIT')]),
    ('C9', '切片/下标丢失', [re.compile(r'BUILD_SLICE'), re.compile(r'SUBSCR')]),
    ('C4', '返回值丢失', [re.compile(r'RETURN_VALUE'), re.compile(r'LOAD_CONST None')]),
    ('C2', '语句/校验被删除',
     [re.compile(r'RAISE_VARARGS'), re.compile(r'LOAD_CONST .*(?:must|invalid|error)'), re.compile(r'CALL \d')]),
    ('C10', 'try/except/else 结构塌陷',
     [re.compile(r'PUSH_EXC_INFO'), re.compile(r'POP_EXCEPT'), re.compile(r'CHECK_EXC_MATCH')]),
]


def classify_unit(unit, fp):
    """返回根因类列表。"""
    diff = unit.get('diff') or []
    txt = '\n'.join(diff)
    tags = []
    # C1：局部名从 STORE_FAST 变成 LOAD_GLOBAL / STORE_ATTR
    for m in re.finditer(r'-\s+STORE_FAST (\w+)', txt):
        name = m.group(1)
        if re.search(r'\+\s+LOAD_GLOBAL %s\b' % re.escape(name), txt) or \
           re.search(r'\+\s+STORE_ATTR', txt) or re.search(r'\+\s+LOAD_GLOBAL \w+', txt):
            tags.append('C1')
            break
    if 'C3' not in tags and ('JUMP_IF_TRUE_OR_POP' in txt and 'JUMP_IF_FALSE_OR_POP' in txt):
        tags.append('C3')
    if 'C5' not in tags and 'AWAIT' in txt:
        tags.append('C5')
    if 'C9' not in tags and 'BUILD_SLICE' in txt:
        tags.append('C9')
    if 'C10' not in tags and ('CHECK_EXC_MATCH' in txt or 'POP_EXCEPT' in txt):
        tags.append('C10')
    if 'C6' not in tags and re.search(r'MAKE_FUNCTION 4\b', txt):
        tags.append('C6')   # MAKE_FUNCTION flag 0x04 = 注解元组
    if 'C12' not in tags and re.search(r'MAKE_FUNCTION 8\b', txt):
        tags.append('C12')  # MAKE_FUNCTION flag 0x08 = 闭包单元
    if not tags and diff:
        # 兜底：仅常量/元组增删 => 语句级差异
        tags.append('C2')
    if not tags and unit.get('note'):
        tags.append('C14')  # 配对失败（code object 无法按 qualname 配对）
    if not tags:
        # 依据 AST 指纹判定
        fd = '; '.join(fp.get('diffs', []))
        if 'await: 源=' in fd and '产物=0' in fd.split('await: 源=')[1][:20]:
            tags.append('C5')
        if 'ann_args: 源=' in fd or 'returns_ann: 源=' in fd:
            tags.append('C6')
        if 'class_body_stmts: 源=' in fd:
            tags.append('C7')
        if 'slice: 源=' in fd:
            tags.append('C9')
        if 'continue: 源=' in fd:
            tags.append('C2')
        if 'boolop: 源=' in fd:
            tags.append('C2')
        if 'return: 源=' in fd:
            tags.append('C4')
    if not tags:
        tags.append('C11')
    return tags


def main() -> int:
    bd = json.load(open(os.path.join(LOGS, 'l4_byte_diff.json'), encoding='utf-8'))['results']
    sd = json.load(open(os.path.join(LOGS, 'l4_source_divergence.json'), encoding='utf-8'))['results']
    fp_by = {}
    for rec in sd:
        for u in rec.get('units', []):
            fp_by[(rec['slug'], u['qualname'])] = u
    out = []
    dist = Counter()
    unit_dist = Counter()
    for rec in bd:
        if rec.get('status') != 'failure':
            continue
        units = []
        for u in rec.get('units', []):
            fp = fp_by.get((rec['slug'], u['qualname']), {})
            tags = classify_unit(u, fp)
            for t in tags:
                unit_dist[t] += 1
            units.append({'qualname': u['qualname'], 'tags': tags,
                          'n_orig_instr': u.get('n_orig_instr'), 'n_prod_instr': u.get('n_prod_instr'),
                          'diff_head': (u.get('diff') or [])[:4]})
        slug_tags = sorted({t for u in units for t in u['tags']})
        for t in slug_tags:
            dist[t] += 1
        out.append({'slug': rec['slug'], 'tags': slug_tags, 'units': units})
    with open(os.path.join(LOGS, 'l4_classify.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'rows': out, 'by_sample': dict(dist), 'by_unit': dict(unit_dist)},
                  f, ensure_ascii=False, indent=1)
    md = ['# L4 失败样本根因分类（§2）', '',
          '| slug | 根因类 | 失败单元数 |', '|---|---|---|']
    for r in out:
        md.append('| `%s` | %s | %d |' % (r['slug'], '、'.join(r['tags']), len(r['units'])))
    md.append('')
    md.append('## 分布（按样本）')
    md.append('')
    for k, v in dist.most_common():
        md.append('- %s: %d' % (k, v))
    md.append('')
    md.append('## 分布（按失败单元）')
    md.append('')
    for k, v in unit_dist.most_common():
        md.append('- %s: %d' % (k, v))
    open(os.path.join(LOGS, 'l4_classify.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(md) + '\n')
    print('[classify] samples=%d 单元=%d' % (len(out), sum(unit_dist.values())))
    for k, v in dist.most_common():
        print('  %-4s %d 样本' % (k, v))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
