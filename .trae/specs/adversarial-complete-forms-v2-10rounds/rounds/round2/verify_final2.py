#!/usr/bin/env python3
"""Round2 最终验证序（回退整改 d8db3448 后）：regen+verify+compare 8 片 + small34 + quotation + tests 六套件。"""
import json
import os
import subprocess
import sys
import time

ROOT = r'F:\Downloads\pythoncdc-main'
ROUND2 = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'rounds', 'round2')
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')
LOG = os.path.join(ROUND2, 'final_verify_log.txt')

SIX_TESTS = [
    'tests/test_algorithm_correctness.py',
    'tests/test_deep_nesting_pressure.py',
    'tests/test_control_flow_completeness_matrix.py',
    'tests/test_complete_syntax_coverage.py',
    'tests/test_boundary_cases.py',
    'tests/test_core_functional.py',
]


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
    sh([sys.executable, 'scripts/pyc_verify.py', 'batch', '--index', os.path.join(BL, 'failing_index.json'),
        '--json', os.path.join(ROUND2, 'small34_report_new.json')], 300, 'SMALL34')
    sh([sys.executable, 'scripts/pyc_verify.py', 'compare', '--before', os.path.join(BL, 'small_test_report.json'),
        '--after', os.path.join(ROUND2, 'small34_report_new.json')], 130, 'SMALL34-CMP')
    sh([sys.executable, 'scripts/pyc_verify.py', 'single', 'site-packages/fly/data/quotation.pyc'], 150, 'QUOTATION')
    sh([sys.executable, '-m', 'pytest'] + SIX_TESTS + ['-q', '--tb=no'], 300, 'TESTS6')
    tot_u = tot_s = tot_f = 0
    for i in range(8):
        rep = json.load(open(os.path.join(ROUND2, 'shard%d_report_new.json' % i), encoding='utf-8'))
        tot_u += rep['units_total']; tot_s += rep['units_success']
        tot_f += rep['files_by_status']['failure']
        print('shard%d: %s units=%s/%s' % (i, rep['files_by_status'], rep['units_success'], rep['units_total']), flush=True)
    print('FINAL: units=%d/%d files_failure=%d total_elapsed=%.0fs' % (tot_s, tot_u, tot_f, time.time() - t00), flush=True)


if __name__ == '__main__':
    main()
