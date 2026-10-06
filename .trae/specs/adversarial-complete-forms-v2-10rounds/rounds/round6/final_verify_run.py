#!/usr/bin/env python3
"""Round6 主代理终验编排（任务 6.4 验证序六步）。
顺序：regen 0-7 → verify 0-6 + shard7 拆分 → compare×8 → small34 → quotation → tests 六套件。
所有子命令超时上限沿用 verify_driver（regen 每文件 90s / verify 290s）。
SMALL34 按 round2 教训直接拆两半执行（单批 301s 曾超时）。
"""
import json
import os
import subprocess
import sys
import time

ROOT = r'F:\Downloads\pythoncdc-main'
ROUND1 = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'rounds', 'round6')
BL = os.path.join(ROOT, '.trae', 'specs', 'adversarial-complete-forms-v2-10rounds', 'baseline')
LOG = os.path.join(ROUND1, 'final_verify_log.txt')

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
    open(LOG, 'w', encoding='utf-8').close()
    t00 = time.time()
    # Phase 1: regen（先删后生成，全部 8 分片）
    for i in range(8):
        sh([sys.executable, os.path.join(ROUND1, 'verify_driver.py'), 'regen', i], 900, 'REGEN%d' % i)
    # Phase 2: verify（0-6 顺序；7 拆分两半）+ compare（基线 = baseline/shards）
    for i in range(7):
        sh([sys.executable, os.path.join(ROUND1, 'verify_driver.py'), 'verify', i], 320, 'VERIFY%d' % i)
        sh([sys.executable, os.path.join(ROUND1, 'verify_driver.py'), 'compare', i], 130, 'COMPARE%d' % i)
    sh([sys.executable, os.path.join(ROUND1, 'verify7_split.py')], 620, 'VERIFY7-SPLIT')
    sh([sys.executable, os.path.join(ROUND1, 'verify_driver.py'), 'compare', 7], 130, 'COMPARE7')
    # Phase 3: small34（34 pyc 小测试集；round2 教训：单批 301s 超时 → 拆两半）
    with open(os.path.join(BL, 'failing_index.json'), encoding='utf-8-sig') as f:
        paths34 = [e['path'] for e in json.load(f)]
    reps = []
    for tag, half in zip(('a', 'b'), (paths34[:17], paths34[17:])):
        out = os.path.join(ROUND1, 'small34_report_%s.json' % tag)
        sh([sys.executable, 'scripts/pyc_verify.py', 'batch', '--json', out] + half,
           300, 'SMALL34-' + tag.upper())
        reps.append(out)
    a = json.load(open(reps[0], encoding='utf-8'))
    b = json.load(open(reps[1], encoding='utf-8'))
    m = dict(a)
    m['rows'] = a.get('rows', []) + b.get('rows', [])
    for k in ('files_total', 'units_total', 'units_success'):
        m[k] = a.get(k, 0) + b.get(k, 0)
    m['success_rate'] = m['units_success'] / m['units_total'] if m['units_total'] else 0.0
    fbs = {}
    for d in (a, b):
        for k, v in d.get('files_by_status', {}).items():
            fbs[k] = fbs.get(k, 0) + v
    m['files_by_status'] = fbs
    pbs = {}
    for d in (a, b):
        for k, v in d.get('paths_by_status', {}).items():
            pbs.setdefault(k, []).extend(v)
    m['paths_by_status'] = pbs
    with open(os.path.join(ROUND1, 'small34_report_new.json'), 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    sh([sys.executable, 'scripts/pyc_verify.py', 'compare', '--before', os.path.join(BL, 'small_test_report.json'),
        '--after', os.path.join(ROUND1, 'small34_report_new.json')], 130, 'SMALL34-CMP')
    # Phase 4: quotation 单验锚点
    sh([sys.executable, 'scripts/pyc_verify.py', 'single', 'site-packages/fly/data/quotation.pyc'], 150, 'QUOTATION')
    # Phase 5: tests 六套件
    sh([sys.executable, '-m', 'pytest'] + SIX_TESTS + ['-q', '--tb=no'], 300, 'TESTS6')
    # 汇总
    tot_u = tot_s = tot_f = 0
    for i in range(8):
        rep = json.load(open(os.path.join(ROUND1, 'shard%d_report_new.json' % i), encoding='utf-8'))
        tot_u += rep['units_total']; tot_s += rep['units_success']
        tot_f += rep['files_by_status']['failure']
        print('shard%d: %s units=%s/%s' % (i, rep['files_by_status'], rep['units_success'], rep['units_total']), flush=True)
    print('FINAL: units=%d/%d files_failure=%d total_elapsed=%.0fs' % (tot_s, tot_u, tot_f, time.time() - t00), flush=True)


if __name__ == '__main__':
    main()