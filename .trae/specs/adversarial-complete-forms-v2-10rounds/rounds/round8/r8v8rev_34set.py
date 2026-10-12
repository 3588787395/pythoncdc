#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 8 淇鎵逛綅A锛?4 灏忔祴璇曢泦锛坔arden-completed-forms-10rounds 鍩虹嚎锛夐噸鏀惧垎鐗囬┍鍔ㄣ€?
RV2 鍙ｅ緞锛氬厛 regen锛坧ycdc -o锛夊啀 batch verify锛坰cripts/pyc_verify.py batch --json锛夈€?鐢ㄦ硶锛歱ython r8v8rev_34set.py <shard> <nshards>  鈥斺€?浜у嚭 r8v8rev_34set_shard<k>.json銆?姹囨€绘瘮瀵瑰熀绾?failing_index.json锛氶€愭枃浠?NEWFAIL锛堟柊澶辫触鍗曞厓锛夊繀椤讳负绌恒€?"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
BASE = os.path.join(ROOT, '.trae', 'specs', 'harden-completed-forms-10rounds', 'baseline', 'failing_index.json')


def run(cmd, timeout=290):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return -9, 'TIMEOUT'


def main():
    shard = int(sys.argv[1]); nshards = int(sys.argv[2])
    entries = json.load(open(BASE, encoding='utf-8'))
    paths = [e['path'] for e in entries]
    k = len(paths)
    idx = [i for i in range(k) if i % nshards == shard]
    rows = []
    for i in idx:
        pyc = paths[i]
        ok = pyc[:-4] + 'OK.py'
        rc, out = run([sys.executable, os.path.join(ROOT, 'pycdc.py'), pyc, '-o', ok])
        if rc != 0:
            print('PYCDC FAIL', pyc, out.strip()[-150:])
        rows.append({'path': pyc})
    idx_path = os.path.join(HERE, 'r8v8rev_34set_shard%d_index.json' % shard)
    with open(idx_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    rep = os.path.join(HERE, 'r8v8rev_34set_shard%d.json' % shard)
    rc, out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
                   'batch', '--index', idx_path, '--json', rep])
    print('shard %d/%d rc=%d' % (shard, nshards, rc))
    print('\n'.join(out.strip().splitlines()[-3:]))


if __name__ == '__main__':
    main()

