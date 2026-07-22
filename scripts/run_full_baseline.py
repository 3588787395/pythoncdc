#!/usr/bin/env python3
"""Phase 0.1: 全测试集基线运行脚本

扫描所有测试目录，运行并统计通过/失败/跳过/错误，生成基线报告。
不修改任何测试，仅运行并归档结果。

覆盖目录（按规范 tasks.md Task 0.1）：
- tests/exhaustive/{if_region,loop,with_region,try_except,match_region,
  boolop,bool_op,ternary,nested,basic,L1_basic,L2_two_level_nested,
  L3_deep_nested,L2_nested,P1_expressions,structured,triple_nested,
  while_loop,for_loop,control_flow_matrix}
- tests/control_flow_matrix/
- tests/nook/
- tests/completeness/
- ok/ + testqouter/round{1,2,3}/ （若存在）
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from collections import OrderedDict

ROOT = Path(__file__).parent.parent
REPORT_DIR = ROOT / '.trae' / 'specs' / 'region-algorithm-deep-iteration'
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# 测试目录映射：目录 -> 类别
TEST_DIRS = OrderedDict([
    # exhaustive 下的子目录
    ('tests/exhaustive/if_region', 'IF'),
    ('tests/exhaustive/while_loop', 'LOOP'),
    ('tests/exhaustive/for_loop', 'LOOP'),
    ('tests/exhaustive/with_region', 'WITH'),
    ('tests/exhaustive/try_except', 'TRY'),
    ('tests/exhaustive/match_region', 'MATCH'),
    ('tests/exhaustive/boolop', 'BOOLOP'),
    ('tests/exhaustive/bool_op', 'BOOLOP'),
    ('tests/exhaustive/ternary', 'TERNARY'),
    ('tests/exhaustive/nested', 'NESTED'),
    ('tests/exhaustive/basic', 'BASIC'),
    ('tests/exhaustive/L1_basic', 'L1'),
    ('tests/exhaustive/L2_basic', 'L1'),
    ('tests/exhaustive/L2_two_level_nested', 'L2'),
    ('tests/exhaustive/L2_nested', 'L2'),
    ('tests/exhaustive/L3_deep_nested', 'L3'),
    ('tests/exhaustive/L3_nested', 'L3'),
    ('tests/exhaustive/triple_nested', 'L3'),
    ('tests/exhaustive/P1_expressions', 'P1'),
    ('tests/exhaustive/structured', 'STRUCTURED'),
    ('tests/exhaustive/control_flow_matrix', 'MATRIX'),
    # 其他测试目录
    ('tests/control_flow_matrix', 'MATRIX'),
    ('tests/completeness', 'COMPLETENESS'),
    ('tests/nook', 'NOOK'),
])


def run_pytest(test_dir: str) -> dict:
    """运行单个测试目录，返回统计结果"""
    full_dir = ROOT / test_dir
    if not full_dir.exists():
        return {'status': 'missing', 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0, 'failures': []}
    cmd = [
        sys.executable, '-m', 'pytest', str(full_dir),
        '-q', '--tb=line', '--no-header', '-p', 'no:cacheprovider',
        '--color=no',
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0, 'failures': []}

    # 从 stdout 末尾解析总结行（pytest 最后一行）
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    summary_line = lines[-1] if lines else ''

    passed = failed = skipped = errors = 0
    import re
    m = re.search(r'(\d+) passed', summary_line)
    if m: passed = int(m.group(1))
    m = re.search(r'(\d+) failed', summary_line)
    if m: failed = int(m.group(1))
    m = re.search(r'(\d+) skipped', summary_line)
    if m: skipped = int(m.group(1))
    m = re.search(r'(\d+) error', summary_line)
    if m: errors = int(m.group(1))

    # 从 stdout 收集失败用例名（FAILED 行）
    failures = []
    for line in lines:
        if line.startswith('FAILED '):
            failures.append(line[len('FAILED '):].strip())
        elif line.startswith('ERROR '):
            failures.append(line[len('ERROR '):].strip())

    return {
        'status': 'ok',
        'passed': passed, 'failed': failed, 'skipped': skipped, 'errors': errors,
        'summary': summary_line,
        'failures': failures,
    }


def main():
    print('=' * 70)
    print('Phase 0.1: 全测试集基线建立')
    print('=' * 70)
    report = OrderedDict()
    total = {'passed': 0, 'failed': 0, 'skipped': 0, 'errors': 0}
    for test_dir, category in TEST_DIRS.items():
        print(f'\n[{category}] {test_dir}', flush=True)
        result = run_pytest(test_dir)
        report[test_dir] = {'category': category, **result}
        if result['status'] == 'ok':
            total['passed'] += result['passed']
            total['failed'] += result['failed']
            total['skipped'] += result['skipped']
            total['errors'] += result['errors']
            print(f'  -> {result["summary"]} ({result["passed"]}p/{result["failed"]}f/{result["skipped"]}s/{result["errors"]}e)')
        else:
            print(f'  -> {result["status"]}')

    print('\n' + '=' * 70)
    print(f'总计: {total["passed"]} passed, {total["failed"]} failed, '
          f'{total["skipped"]} skipped, {total["errors"]} errors')
    print('=' * 70)

    # 保存 JSON 报告
    out_json = REPORT_DIR / 'baseline_report.json'
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'total': total, 'by_dir': report}, f, ensure_ascii=False, indent=2)
    print(f'\n基线报告已保存: {out_json}')

    # 保存失败用例清单
    out_failures = REPORT_DIR / 'baseline_failures.txt'
    with open(out_failures, 'w', encoding='utf-8') as f:
        for test_dir, info in report.items():
            if info.get('failures'):
                f.write(f'\n# [{info["category"]}] {test_dir} ({info["failed"]} failed, {info["errors"]} errors)\n')
                for nodeid in info['failures']:
                    f.write(f'{nodeid}\n')
    print(f'失败用例清单已保存: {out_failures}')


if __name__ == '__main__':
    main()
