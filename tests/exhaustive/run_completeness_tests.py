#!/usr/bin/env python3
"""
CFG反编译器完备性测试运行器 V5
自动运行所有区域类型的测试用例并生成详细报告

功能特性:
- 自动发现并运行所有完备性测试用例
- 按区域类型分类统计通过/失败/错误数量
- 生成详细的文本报告和JSON报告
- 支持目标达成率对比分析
- 支持命令行参数控制（--type, --verbose, --output, --format）
"""

import unittest
import sys
import os
import time
import json
import importlib
import importlib.util
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.exhaustive.base import ExhaustiveTestCase

TEST_DIRS = {
    'basic': 'tests/exhaustive/basic/',
    'if_region': 'tests/exhaustive/if_region/',
    'for_loop': 'tests/exhaustive/for_loop/',
    'while_loop': 'tests/exhaustive/while_loop/',
    'try_except': 'tests/exhaustive/try_except/',
    'with_region': 'tests/exhaustive/with_region/',
    'nested': 'tests/exhaustive/nested/',
    'match_region': 'tests/exhaustive/match_region/',
    'boolop': 'tests/exhaustive/boolop/',
    'ternary': 'tests/exhaustive/ternary/',
}

EXHAUSTIVE_DIR = os.path.dirname(os.path.abspath(__file__))

TARGETS = {
    'basic': {'target': 85, 'description': '基础语句'},
    'if_region': {'target': 97, 'description': '条件分支'},
    'for_loop': {'target': 85, 'description': 'for循环'},
    'while_loop': {'target': 100, 'description': 'while循环'},
    'try_except': {'target': 75, 'description': '异常处理'},
    'match_region': {'target': 85, 'description': '模式匹配'},
    'boolop': {'target': 80, 'description': '布尔运算'},
    'ternary': {'target': 85, 'description': '三元表达式'},
    'nested': {'target': 80, 'description': '嵌套结构'},
    'with_region': {'target': 80, 'description': '上下文管理'},
}


class CompletenessTestRunner:
    """完备性测试运行器"""

    def __init__(self, output_file: str = 'full_report_v5.txt'):
        self.output_file = output_file
        self.results: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total': 0, 'passed': 0, 'failed': 0,
            'error': 0, 'skipped': 0, 'errors': [], 'tests': []
        })
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0
        self.total_error = 0
        self.total_skipped = 0

    def discover_tests(self, test_dir: str) -> List[Tuple[str, str]]:
        """发现指定目录下的所有测试文件"""
        test_files = []
        if not os.path.isdir(test_dir):
            return test_files

        for filename in sorted(os.listdir(test_dir)):
            if filename.startswith('test_') and filename.endswith('.py'):
                filepath = os.path.join(test_dir, filename)
                test_files.append((filename, filepath))

        return test_files

    def load_test_class(self, filepath: str) -> Optional[type]:
        """加载测试文件中的测试类"""
        module_name = f'completeness_test_{os.path.splitext(os.path.basename(filepath))[0]}'

        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"  警告: 加载模块失败 {filepath}: {e}")
            return None

        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                    issubclass(obj, ExhaustiveTestCase) and
                    obj is not ExhaustiveTestCase):
                return obj

        return None

    def run_single_test(self, test_class: type, verbose: bool = False) -> Tuple[str, Optional[str], float]:
        """运行单个测试用例"""
        start_time = time.time()

        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(
            stream=open(os.devnull, 'w') if not verbose else sys.stdout,
            verbosity=2 if verbose else 0
        )
        result = runner.run(suite)

        duration = time.time() - start_time

        if result.wasSuccessful():
            return ('passed', None, duration)
        elif result.errors:
            error_msg = str(result.errors[0][1])[:500]
            return ('error', error_msg, duration)
        elif result.failures:
            failure_msg = str(result.failures[0][1])[:500]
            return ('failed', failure_msg, duration)
        else:
            return ('skipped', None, duration)

    def run_all(self, test_type: Optional[str] = None, verbose: bool = False):
        """运行所有或指定类型的测试"""
        self.start_time = time.time()

        if test_type and test_type in TEST_DIRS:
            dirs_to_run = {test_type: TEST_DIRS[test_type]}
        else:
            dirs_to_run = TEST_DIRS

        print("\n" + "=" * 80)
        print("CFG反编译器完备性测试框架 V5")
        print("=" * 80)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标区域类型: {', '.join(dirs_to_run.keys())}")
        print("=" * 80 + "\n")

        total_files = 0
        for type_name, dir_path in dirs_to_run.items():
            test_files = self.discover_tests(dir_path)
            total_files += len(test_files)

            if not test_files:
                print(f"[{type_name}] 未找到测试文件")
                continue

            print(f"\n{'='*60}")
            print(f"Running {type_name} tests ({len(test_files)} files)...")
            print(f"{'='*60}")

            for i, (filename, filepath) in enumerate(test_files, 1):
                if verbose:
                    print(f"\n[{i}/{len(test_files)}] {type_name}/{filename}", end=" ", flush=True)

                test_class = self.load_test_class(filepath)
                if test_class is None:
                    if verbose:
                        print("SKIP (无法加载)")
                    self.results[type_name]['skipped'] += 1
                    self.total_skipped += 1
                    self.results[type_name]['total'] += 1
                    self.total_tests += 1
                    continue

                try:
                    status, error, duration = self.run_single_test(test_class, verbose)

                    self.results[type_name]['total'] += 1
                    self.total_tests += 1
                    self.results[type_name]['tests'].append({
                        'name': filename,
                        'status': status,
                        'duration': duration,
                        'error': error
                    })

                    if status == 'passed':
                        self.results[type_name]['passed'] += 1
                        self.total_passed += 1
                        if verbose:
                            print("PASS")
                    elif status == 'failed':
                        self.results[type_name]['failed'] += 1
                        self.total_failed += 1
                        if error:
                            self.results[type_name]['errors'].append({
                                'test': filename,
                                'error': error
                            })
                        if verbose:
                            print("FAIL")
                            if error:
                                print(f"  Error: {error[:200]}")
                    elif status == 'error':
                        self.results[type_name]['error'] += 1
                        self.total_error += 1
                        if error:
                            self.results[type_name]['errors'].append({
                                'test': filename,
                                'error': error
                            })
                        if verbose:
                            print("ERROR")
                            if error:
                                print(f"  Error: {error[:200]}")
                    else:
                        self.results[type_name]['skipped'] += 1
                        self.total_skipped += 1
                        if verbose:
                            print("SKIP")

                except Exception as e:
                    self.results[type_name]['error'] += 1
                    self.total_error += 1
                    self.results[type_name]['total'] += 1
                    self.total_tests += 1
                    self.results[type_name]['errors'].append({
                        'test': filename,
                        'error': str(e)
                    })
                    if verbose:
                        print(f"EXCEPTION: {e}")

        self.end_time = time.time()
        elapsed_time = self.end_time - self.start_time

        print(f"\n\n{'='*80}")
        print(f"测试完成! 共处理 {total_files} 个测试文件")
        print(f"总耗时: {elapsed_time:.2f}秒")
        print('=' * 80)

        return elapsed_time

    def generate_text_report(self, elapsed_time: float) -> str:
        """生成详细文本报告"""
        lines = []

        lines.append("=" * 80)
        lines.append("CFG反编译器完备性测试报告 V5")
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"总耗时: {elapsed_time:.2f}秒")
        lines.append("=" * 80)
        lines.append("")

        # 汇总统计
        lines.append("📊 汇总统计")
        lines.append("-" * 80)
        lines.append(f"{'区域类型':<20} {'描述':<12} {'总数':>8} {'通过':>8} {'失败':>8} {'错误':>8} {'跳过':>8} {'通过率':>10}")
        lines.append("-" * 80)

        for type_name in sorted(TEST_DIRS.keys()):
            if type_name in self.results and self.results[type_name]['total'] > 0:
                stats = self.results[type_name]
                target_info = TARGETS.get(type_name, {})
                desc = target_info.get('description', '')
                rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0

                lines.append(
                    f"{type_name:<20} {desc:<12} "
                    f"{stats['total']:>8} {stats['passed']:>8} "
                    f"{stats['failed']:>8} {stats['error']:>8} "
                    f"{stats['skipped']:>8} {rate:>9.1f}%"
                )

        lines.append("-" * 80)

        overall_rate = (self.total_passed / self.total_tests * 100) if self.total_tests > 0 else 0
        lines.append(
            f"{'总计':<20} {'':<12} "
            f"{self.total_tests:>8} {self.total_passed:>8} "
            f"{self.total_failed:>8} {self.total_error:>8} "
            f"{self.total_skipped:>8} {overall_rate:>9.1f}%"
        )

        lines.append("")
        lines.append("")

        # 目标对比
        lines.append("🎯 目标达成情况")
        lines.append("-" * 80)
        lines.append(f"{'区域类型':<20} {'目标':>10} {'实际':>10} {'差距':>10} {'状态':>12}")
        lines.append("-" * 80)

        achieved_count = 0
        total_targets = 0

        for type_name, target_info in TARGETS.items():
            if type_name in self.results and self.results[type_name]['total'] > 0:
                stats = self.results[type_name]
                target_rate = target_info['target']
                actual_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                diff = actual_rate - target_rate
                status = "✅ 达成" if actual_rate >= target_rate else "❌ 未达标"

                if actual_rate >= target_rate:
                    achieved_count += 1
                total_targets += 1

                lines.append(
                    f"{type_name:<20} {target_rate:>9}% {actual_rate:>9}% "
                    f"{diff:>+9}% {status:>12}"
                )

        lines.append("-" * 80)
        achievement_rate = (achieved_count / total_targets * 100) if total_targets > 0 else 0
        lines.append(f"目标达成率: {achieved_count}/{total_targets} ({achievement_rate:.1f}%)")

        lines.append("")
        lines.append("")

        # 失败详情
        all_errors = []
        for type_name, stats in self.results.items():
            if stats['errors']:
                for err in stats['errors']:
                    all_errors.append((type_name, err))

        if all_errors:
            lines.append("⚠️  失败/错误详情 (前20个)")
            lines.append("-" * 80)

            for i, (type_name, err_info) in enumerate(all_errors[:20], 1):
                error_str = err_info['error'][:150] if err_info['error'] else ''
                lines.append(f"{i}. [{type_name}] {err_info['test']}")
                lines.append(f"   错误: {error_str}")
                lines.append("")

            if len(all_errors) > 20:
                lines.append(f"... 还有 {len(all_errors) - 20} 个错误未显示")

        lines.append("")
        lines.append("")

        # 评估等级
        lines.append("📈 总体评估")
        lines.append("-" * 80)

        if overall_rate >= 95:
            grade = "★★★★★ 优秀 (>=95%)"
        elif overall_rate >= 85:
            grade = "★★★★☆ 良好 (>=85%)"
        elif overall_rate >= 70:
            grade = "★★★☆☆ 一般 (>=70%)"
        elif overall_rate >= 50:
            grade = "★★☆☆☆ 较差 (>=50%)"
        else:
            grade = "★☆☆☆☆ 差 (<50%)"

        lines.append(f"总体通过率: {overall_rate:.2f}%")
        lines.append(f"评估等级: {grade}")
        lines.append(f"目标达成率: {achievement_rate:.1f}%")

        lines.append("")
        lines.append("=" * 80)
        lines.append("报告结束")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_json_report(self, elapsed_time: float) -> dict:
        """生成JSON格式报告"""
        report = {
            'metadata': {
                'version': '5.0',
                'timestamp': datetime.now().isoformat(),
                'duration': elapsed_time,
                'generator': 'CompletenessTestRunner'
            },
            'summary': {
                'total_tests': self.total_tests,
                'passed': self.total_passed,
                'failed': self.total_failed,
                'errors': self.total_error,
                'skipped': self.total_skipped,
                'pass_rate': round(self.total_passed / max(self.total_tests, 1) * 100, 2),
            },
            'targets': {},
            'by_region_type': {},
            'errors': []
        }

        # 目标对比
        for type_name, target_info in TARGETS.items():
            if type_name in self.results and self.results[type_name]['total'] > 0:
                stats = self.results[type_name]
                actual_rate = round(stats['passed'] / max(stats['total'], 1) * 100, 2)
                report['targets'][type_name] = {
                    'target': target_info['target'],
                    'actual': actual_rate,
                    'achieved': actual_rate >= target_info['target'],
                    'description': target_info.get('description', '')
                }

        # 各区域类型统计
        for type_name, stats in self.results.items():
            if stats['total'] > 0:
                report['by_region_type'][type_name] = {
                    'total': stats['total'],
                    'passed': stats['passed'],
                    'failed': stats['failed'],
                    'errors': stats['error'],
                    'skipped': stats['skipped'],
                    'pass_rate': round(stats['passed'] / max(stats['total'], 1) * 100, 2),
                    'test_details': stats['tests']
                }

        # 收集所有错误
        for type_name, stats in self.results.items():
            if stats['errors']:
                for err in stats['errors']:
                    report['errors'].append({
                        'region_type': type_name,
                        'test': err['test'],
                        'error': err['error']
                    })

        return report

    def generate_report(self, elapsed_time: float, output_format: str = 'text'):
        """生成并保存报告"""
        if output_format == 'json':
            report_data = self.generate_json_report(elapsed_time)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ JSON报告已生成: {self.output_file}")
        else:
            report_text = self.generate_text_report(elapsed_time)
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n✅ 文本报告已生成: {self.output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='CFG反编译器完备性测试运行器 V5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_completeness_tests.py                          # 运行所有测试
  python run_completeness_tests.py --type basic             # 只运行basic类型
  python run_completeness_tests.py --verbose                # 详细输出
  python run_completeness_tests.py --output myreport.txt    # 自定义输出文件名
  python run_completeness_tests.py --format json            # JSON格式输出
  python run_completeness_tests.py --type if_region --verbose --output if_report.txt

支持的测试类型:
  basic       - 基础语句 (赋值、返回、导入等)
  if_region   - 条件分支 (if/elif/else)
  for_loop    - for循环
  while_loop  - while循环
  try_except  - 异常处理 (try/except/finally)
  with_region - 上下文管理 (with语句)
  nested      - 嵌套结构
  match_region- 模式匹配 (match/case)
  boolop      - 布尔运算 (and/or/not)
  ternary     - 三元表达式
        """
    )

    parser.add_argument(
        '--type', '-t',
        choices=TEST_DIRS.keys(),
        help='只运行指定类型的测试'
    )

    parser.add_argument(
        '--output', '-o',
        default='full_report_v5.txt',
        help='输出报告文件名 (默认: full_report_v5.txt)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出（每个测试的结果）'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='输出格式: text (默认) 或 json'
    )

    args = parser.parse_args()

    runner = CompletenessTestRunner(output_file=args.output)
    elapsed_time = runner.run_all(test_type=args.type, verbose=args.verbose)

    # 生成报告
    runner.generate_report(elapsed_time, args.format)

    # 打印摘要到控制台
    print("\n" + "-" * 80)
    print("快速摘要:")
    print(f"  总测试数: {runner.total_tests}")
    print(f"  通过: {runner.total_passed} ({runner.total_passed/max(runner.total_tests,1)*100:.1f}%)")
    print(f"  失败: {runner.total_failed}")
    print(f"  错误: {runner.total_error}")
    print(f"  跳过: {runner.total_skipped}")
    print("-" * 80)

    # 返回退出码
    total_issues = runner.total_failed + runner.total_error
    if total_issues > 0:
        print(f"\n⚠️  存在 {total_issues} 个问题，退出码: 1")
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过！退出码: 0")
        sys.exit(0)


if __name__ == '__main__':
    main()
