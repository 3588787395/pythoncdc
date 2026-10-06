#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round4 复核（Task 4.3）：独立复跑读数 vs 上一批读数逐单元比对，判定 NEWFAIL。

NEWFAIL = 真实 success -> failure 回退（某单元在旧批次通过、本批次失败）。
判据：
  ① 文件级：旧 status=success（无失败单元）且新 status=failure → 全量回退，NEWFAIL。
  ② 单元级：旧 failures 集合 F0、新 failures 集合 F1；extra = F1 - F0 即本批次新增失败。
输出 r4v4r_newfail.json。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(HERE, 'r4v4_probe_full.json')
NEW = os.path.join(HERE, 'r4v4r_probe_full.json')


def norm(p):
    return p.replace('\\', '/').replace('F:/Downloads/pythoncdc-main/', '')


def load(path):
    d = json.load(open(path, encoding='utf-8'))
    return {norm(e['pyc']): e for e in d}


def main():
    old, new = load(OLD), load(NEW)
    rows = []
    newfail_files = []
    for p in sorted(set(old) & set(new)):
        o, n = old[p], new[p]
        extra = sorted(set(n.get('failures', [])) - set(o.get('failures', [])))
        missing = sorted(set(o.get('failures', [])) - set(n.get('failures', [])))
        if o.get('status') in ('success', 'compile_error') or True:
            pass
        is_reg = bool(extra)
        # 文件级强判：旧 success（无失败）→ 新 failure
        hard = (o.get('status') == 'success' and n.get('status') == 'failure')
        if is_reg or hard:
            newfail_files.append(p)
        rows.append({
            'pyc': p, 'old_status': o.get('status'), 'new_status': n.get('status'),
            'old_units': '%s/%s' % (o.get('units_success'), o.get('units_total')),
            'new_units': '%s/%s' % (n.get('units_success'), n.get('units_total')),
            'new_failures': extra, 'improved_missing': missing,
            'NEWFAIL': is_reg or hard,
        })
    out = {'OLD': norm(OLD), 'NEW': norm(NEW), 'newfail_count': len(newfail_files),
           'newfail_files': newfail_files, 'rows': rows}
    with open(os.path.join(HERE, 'r4v4r_newfail.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for r in rows:
        flag = 'NEWFAIL' if r['NEWFAIL'] else ('improved' if r['improved_missing'] else 'same')
        print('%-9s %-40s %s->%s new=%s miss=%s' % (
            flag, r['pyc'], r['old_units'], r['new_units'],
            len(r['new_failures']), len(r['improved_missing'])))
    print('-> NEWFAIL count = %d' % len(newfail_files))


if __name__ == '__main__':
    main()