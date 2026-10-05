#!/usr/bin/env python3
"""Round2 主代理验证序补跑（regen 无预删版）：regen 0-7 → verify 0-6 + shard7 拆分 → compare 0-7。
复用 final_verify_run.py 的分步与日志口径；regen 已改为 pyccdc 覆盖写（见 verify_driver.py 注记）。
"""
import json
import os
import subprocess
import sys
import time

ROOT = r'F:\Downloads\pythoncdc-main'
ROUND2 = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'rounds', 'round2')
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')
LOG = os.path.join(ROUND2, 'final_verify_log.txt')


def sh(args, timeout, label):
    t0 = time.time()
    try:
        r = subprocess.run([str(a) for a in args], cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=timeout)
        rc, out = r.returncode, (r.stdout or '') + (('\n[stderr] ' + r.stderr) if r.stderr else '')
    except subprocess.TimeoutExpired as e:
        rc, out = 'TIMEOUT', '[TIMEOUT] %s' % str(e)[:300]
    line = '=== %s rc=%s %.1fs' % (label, rc, time.time() - t0)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n' + out[-1500:] + '\n')
    print(line, flush=True)
    return rc, out


def main():
    t00 = time.time()
    for i in range(8):
        sh([sys.executable, os.path.join(ROUND2, 'verify_driver.py'), 'regen', i], 900, 'REGEN%d' % i)
    for i in range(7):
        sh([sys.executable, os.path.join(ROUND2, 'verify_driver.py'), 'verify', i], 320, 'VERIFY%d' % i)
        sh([sys.executable, os.path.join(ROUND2, 'verify_driver.py'), 'compare', i], 130, 'COMPARE%d' % i)
    sh([sys.executable, os.path.join(ROUND2, 'verify7_split.py')], 620, 'VERIFY7-SPLIT')
    sh([sys.executable, os.path.join(ROUND2, 'verify_driver.py'), 'compare', 7], 130, 'COMPARE7')
    tot_u = tot_s = tot_f = 0
    for i in range(8):
        rep = json.load(open(os.path.join(ROUND2, 'shard%d_report_new.json' % i), encoding='utf-8'))
        tot_u += rep['units_total']; tot_s += rep['units_success']
        tot_f += rep['files_by_status']['failure']
        print('shard%d: %s units=%s/%s' % (i, rep['files_by_status'], rep['units_success'], rep['units_total']), flush=True)
    print('FINAL: units=%d/%d files_failure=%d total_elapsed=%.0fs' % (tot_s, tot_u, tot_f, time.time() - t00), flush=True)


if __name__ == '__main__':
    main()
