#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 三段承重面门禁：B126-R2 修复后全量承重（RV2 临时产物，不写 *OK.py）。

证据：r9v9fix3_bearing.json。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
OUT = os.path.join(HERE, 'r9v9fix3_bearing.json')
TMPOUT = r'D:\Temp\opencode\r93_products'

TARGETS = [
    ('broker', 'site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc', 128),
    ('matcher', 'site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc', 17),
    ('finance', 'site-packages/IQCommon/data/finance.pyc', 32),
    ('quote_handler', 'site-packages/fly/data/quote_handler.pyc', 79),
    ('realtime', 'site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc', 13),
    ('quotation', 'site-packages/fly/data/quotation.pyc', 153),
    ('nb_for', r'D:\Temp\mon\nb\nb_for.pyc', 2),
    ('nb_with', r'D:\Temp\mon\nb\nb_with.pyc', 2),
    ('nb_while', r'D:\Temp\mon\nb\nb_while.pyc', None),
    ('nb_b99', r'D:\Temp\mon\nb\nb_b99.pyc', 4),
]

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')


def run(cmd, timeout=250):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'


def one(name, rel):
    full = rel if os.path.isabs(rel) else os.path.join(ROOT, rel.replace('/', os.sep))
    os.makedirs(TMPOUT, exist_ok=True)
    ok = os.path.join(TMPOUT, 'fix2_' + name + '.py')
    r = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    regen_rc_ok = ('TIMEOUT' not in r)
    out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
               'single', full, '--source', ok])
    status, us, ut = None, None, None
    for line in out.splitlines():
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    return {'name': name, 'pyc': rel, 'status': status,
            'units_success': us, 'units_total': ut, 'regen_ok': regen_rc_ok}


def main():
    only = set(sys.argv[1:])
    rows = []
    for name, rel, exp in TARGETS:
        if only and name not in only:
            continue
        if not os.path.exists(rel if os.path.isabs(rel) else
                               os.path.join(ROOT, rel.replace('/', os.sep))):
            print('[%-14s] SKIP missing' % name, flush=True)
            continue
        r = one(name, rel)
        rows.append(r)
        print('[%-14s] %-8s %s/%s (exp %s)' % (name, r['status'], r['units_success'],
                                               r['units_total'], exp), flush=True)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print('-> ' + os.path.basename(OUT))


if __name__ == '__main__':
    main()
