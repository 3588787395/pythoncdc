#!/usr/bin/env python3
"""Round1 主代理全量验证驱动（复用 round10 流程）（归档工具，不进 scripts/）。
用法:
  python verify_driver.py regen <shard> [start] [end]   # 重生成该分片全部 OK.py（先删后生成，失败记录）
  python verify_driver.py verify <shard>               # pyc_verify batch 该分片 → shardN_report_new.json
  python verify_driver.py compare <shard>              # compare 基线 vs 新报告（Movement Matrix）
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline', 'shards')


def shard_paths(n):
    with open(os.path.join(BL, 'shard%d.json' % n), encoding='utf-8-sig') as f:
        return [e['path'] for e in json.load(f)]


def ok_path(pyc):
    return pyc[:-4] + 'OK.py'


def cmd_regen(n, start, end):
    paths = shard_paths(n)[start:end]
    if end is None:
        end = start + len(paths)
    failed = []
    for i, pyc in enumerate(paths):
        ok = ok_path(pyc)
        # round2 调整：不预删（safe-delete 守卫拦截批量 os.remove）；pycdc -o 对既有文件
        # 为截断覆盖写，等价先删后生成；pycdc 失败仍记入 failed，verify 阶段据此排除。
        if not os.path.exists(ok):
            pass
        try:
            r = subprocess.run([sys.executable, 'pycdc.py', '-o', ok, pyc],
                               cwd=ROOT, capture_output=True, text=True,
                               timeout=90, encoding='utf-8', errors='replace')
            if r.returncode != 0 or not os.path.exists(ok):
                failed.append({'path': pyc, 'rc': r.returncode,
                               'err': (r.stderr or r.stdout)[-400:]})
                print('[FAIL] %s rc=%s' % (pyc, r.returncode))
        except subprocess.TimeoutExpired:
            failed.append({'path': pyc, 'rc': 'timeout', 'err': ''})
            print('[TIMEOUT] %s' % pyc)
    out = os.path.join(HERE, 'regen_shard%d.json' % n)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(failed, f, ensure_ascii=False, indent=1)
    print('regen shard%d [%d:%d]: %d ok, %d failed -> %s'
          % (n, start, end, len(paths) - len(failed), len(failed), out))


def verify_paths(n):
    paths = shard_paths(n)
    regen_fail = {e['path'] for e in _load(os.path.join(HERE, 'regen_shard%d.json' % n), [])}
    return [p for p in paths if p not in regen_fail]


def _load(p, dflt):
    if not os.path.exists(p):
        return dflt
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def cmd_verify(n):
    paths = verify_paths(n)
    rep = os.path.join(HERE, 'shard%d_report_new.json' % n)
    r = subprocess.run([sys.executable, 'scripts/pyc_verify.py', 'batch',
                        '--json', rep] + paths,
                       cwd=ROOT, capture_output=True, text=True, timeout=290,
                       encoding='utf-8', errors='replace')
    print(r.stdout[-1500:])
    if r.returncode != 0:
        print('[VERIFY RC=%d] %s' % (r.returncode, r.stderr[-800:]))
        sys.exit(r.returncode)
    with open(rep, encoding='utf-8') as f:
        d = json.load(f)
    print('shard%d NEW: %s units=%s/%s' % (n, d['files_by_status'],
                                           d['units_success'], d['units_total']))


def cmd_compare(n):
    old = os.path.join(BL, 'shard%d_report.json' % n)
    new = os.path.join(HERE, 'shard%d_report_new.json' % n)
    r = subprocess.run([sys.executable, 'scripts/pyc_verify.py', 'compare',
                        '--before', old, '--after', new],
                       cwd=ROOT, capture_output=True, text=True, timeout=120,
                       encoding='utf-8', errors='replace')
    print(r.stdout[-2500:])
    if r.returncode != 0:
        print('[COMPARE RC=%d] %s' % (r.returncode, r.stderr[-500:]))


if __name__ == '__main__':
    mode = sys.argv[1]
    n = int(sys.argv[2])
    if mode == 'regen':
        s = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        e = int(sys.argv[4]) if len(sys.argv) > 4 else None
        cmd_regen(n, s, e)
    elif mode == 'verify':
        cmd_verify(n)
    elif mode == 'compare':
        cmd_compare(n)
    else:
        print(__doc__)
