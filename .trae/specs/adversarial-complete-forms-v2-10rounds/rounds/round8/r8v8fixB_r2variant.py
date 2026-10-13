#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round8 整改批（FIX_R2）变体电池复读驱动（RV2：先 regen（pycdc -o）再 verify single）。

只读 core/，只写本目录 r8v8fixB_repro_r2variant.json。复用评审已建变体探针
（test_repros/round8/r8v8rev_* 前缀），不新建探针；刻意排除会挂死/崩溃的
r8v8rev_bmatch_guards_battery（v2 嵌套 match 存量挂死 = B122 域外登记项）与
r8v8rev_bmatch_nestnoguard（n1 同根）——两项均非本轮 5 打回项复验面。

用法：python r8v8fixB_r2variant.py   # 跑全部 7 个打回项复验变体电池
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))

PROBES = {
    # B104-R2a/R2b（REVIEW2 §0#1/#2 打回复验）
    'b104_chain4_battery': 'test_repros/round8/r8v8rev_b104_chain4_battery.pyc',
    # B105-R2（§0#3）
    'b105_walrus_battery': 'test_repros/round8/r8v8rev_b105_walrus_battery.pyc',
    # B107-R2（§0#4）
    'b107_mtarget3_battery': 'test_repros/round8/r8v8rev_b107_mtarget3_battery.pyc',
    'b107_iso_battery': 'test_repros/round8/r8v8rev_b107_iso_battery.pyc',
    'b107_iso2_battery': 'test_repros/round8/r8v8rev_b107_iso2_battery.pyc',
    # B103-R2（§0#5；v3 为 guards 电池的拆分复验探针，避免整电池触发 B122 挂死单元）
    'bmatch_v3': 'test_repros/round8/r8v8rev_bmatch_v3.pyc',
    'bmatch_or3iso': 'test_repros/round8/r8v8rev_bmatch_or3iso.pyc',
}

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def one(name, rel):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok = full[:-4] + 'OK.py'
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'single', full])
    tail = [l for l in out.splitlines() if l.strip()]
    status, us, ut = None, None, None
    for line in tail:
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in tail if FAIL_RE.match(l)]
    return {'name': name, 'pyc': rel, 'status': status, 'units_success': us,
            'units_total': ut, 'failures': fails}


def main():
    rows = []
    for n in PROBES:
        r = one(n, PROBES[n])
        rows.append(r)
        print('[%-22s] %-8s %s/%s' % (n, r['status'], r['units_success'], r['units_total']), flush=True)
        for f in r['failures']:
            print('    ' + f)
    out = os.path.join(HERE, 'r8v8fixB_repro_r2variant.json')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    ok = sum(r['units_success'] or 0 for r in rows)
    tot = sum(r['units_total'] or 0 for r in rows)
    print('-> units=%d/%d  (%d probes)  %s' % (ok, tot, len(rows), os.path.basename(out)))


if __name__ == '__main__':
    main()
