#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
控制流完备性测试运行器和报告生成

功能：
1. 运行所有控制流测试用例
2. 生成详细的测试报告
3. 统计通过/失败/跳过的测试数量
4. 按类别汇总测试结果
5. 支持命令行参数配置

使用方法：
    # 运行所有测试
    python run_tests.py

    # 只运行L1基本结构测试
    python run_tests.py --level L1

    # 生成详细报告
    python run_tests.py --verbose

    # 输出JSON格式报告
    python run_tests.py --format json

    # 运行特定测试类
    python run_tests.py --class TestB01SimpleAssignment
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .base import ControlFlowTestCase


class TestResultCollector(unittest.TextTestRunner):
    """自定义测试结果收集器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detailed_results = []

    def _makeResult(self):
        result = super()._makeResult()
        return result


class TestReportGenerator:
    """测试报告生成器"""

    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {
            'L1': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
            'L1_EXP': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
            'L1_CF': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
            'L2': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
            'L2_EX': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
            'L3': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
            'L3_CO': {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'errors': [], 'tests': []},
        }
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0
        self.total_skipped = 0
        self.total_errors = 0

    def start(self):
        """记录开始时间"""
        self.start_time = time.time()

    def finish(self):
        """记录结束时间"""
        self.end_time = time.time()

    def add_result(self, test_class_name: str, level: str, status: str,
                   error_message: str = None, duration: float = 0):
        """
        添加单个测试结果

        Args:
            test_class_name: 测试类名
            level: 测试级别 (L1/L2/L3)
            status: 状态 (passed/failed/skipped/error)
            error_message: 错误信息（如果有）
            duration: 执行时间（秒）
        """
        if level not in self.results:
            self.results[level] = {
                'total': 0, 'passed': 0, 'failed': 0,
                'skipped': 0, 'errors': [], 'tests': []
            }

        self.results[level]['total'] += 1
        self.total_tests += 1

        test_info = {
            'name': test_class_name,
            'status': status,
            'duration': duration,
            'error': error_message
        }

        if status == 'passed':
            self.results[level]['passed'] += 1
            self.total_passed += 1
        elif status == 'failed':
            self.results[level]['failed'] += 1
            self.total_failed += 1
            if error_message:
                self.results[level]['errors'].append({
                    'test': test_class_name,
                    'error': error_message
                })
        elif status == 'skipped':
            self.results[level]['skipped'] += 1
            self.total_skipped += 1
        elif status == 'error':
            self.results[level]['failed'] += 1
            self.total_errors += 1
            if error_message:
                self.results[level]['errors'].append({
                    'test': test_class_name,
                    'error': error_message
                })

        self.results[level]['tests'].append(test_info)

    def generate_text_report(self) -> str:
        """生成文本格式的报告"""
        lines = []
        lines.append("=" * 80)
        lines.append("Python 控制流完备性测试报告")
        lines.append("=" * 80)
        lines.append("")

        # 时间信息
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            lines.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"执行时长: {duration:.2f} 秒")
        lines.append("")

        # 总体统计
        lines.append("-" * 80)
        lines.append("总体统计")
        lines.append("-" * 80)
        lines.append(f"总测试数: {self.total_tests}")
        lines.append(f"通过:     {self.total_passed} ({self.total_tests * 100 / max(self.total_tests, 1):.1f}%)")
        lines.append(f"失败:     {self.total_failed} ({self.total_tests * 100 / max(self.total_tests, 1):.1f}%)")
        lines.append(f"跳过:     {self.total_skipped} ({self.total_tests * 100 / max(self.total_tests, 1):.1f}%)")
        lines.append(f"错误:     {self.total_errors}")
        lines.append("")

        # 各级别统计
        lines.append("-" * 80)
        lines.append("各级别统计")
        lines.append("-" * 80)

        for level in ['L1', 'L1_EXP', 'L1_CF', 'L2', 'L2_EX', 'L3', 'L3_CO']:
            if level in self.results:
                stats = self.results[level]
                total = stats['total']
                passed = stats['passed']
                failed = stats['failed']
                skipped = stats['skipped']

                pass_rate = passed * 100 / max(total, 1)

                lines.append(f"\n{level} 级别测试:")
                lines.append(f"  总数:   {total}")
                lines.append(f"  通过:   {passed} ({pass_rate:.1f}%)")
                lines.append(f"  失败:   {failed}")
                lines.append(f"  跳过:   {skipped}")

                if stats['errors']:
                    lines.append(f"\n  失败的测试:")
                    for err in stats['errors']:
                        lines.append(f"    - {err['test']}: {err['error'][:100]}...")

        lines.append("")
        lines.append("-" * 80)

        # 通过率评估
        overall_pass_rate = self.total_passed * 100 / max(self.total_tests, 1)
        lines.append("\n总体评估:")

        if overall_pass_rate >= 95:
            lines.append("  ★★★★★ 优秀 (>=95%) - 控制流反编译能力非常完善")
        elif overall_pass_rate >= 85:
            lines.append("  ★★★★☆ 良好 (>=85%) - 控制流反编译能力较好，有少量问题")
        elif overall_pass_rate >= 70:
            lines.append("  ★★★☆☆ 一般 (>=70%) - 控制流反编译能力一般，需要改进")
        elif overall_pass_rate >= 50:
            lines.append("  ★★☆☆☆ 较差 (>=50%) - 控制流反编译能力较差，需要重点改进")
        else:
            lines.append("  ★☆☆☆☆ 差 (<50%) - 控制流反编译能力很差，需要全面修复")

        lines.append(f"\n通过率: {overall_pass_rate:.2f}%")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_json_report(self) -> dict:
        """生成JSON格式的报告"""
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'duration': (self.end_time or time.time()) - (self.start_time or time.time()),
                'version': '1.0.0'
            },
            'summary': {
                'total': self.total_tests,
                'passed': self.total_passed,
                'failed': self.total_failed,
                'skipped': self.total_skipped,
                'errors': self.total_errors,
                'pass_rate': self.total_passed * 100 / max(self.total_tests, 1)
            },
            'by_level': {}
        }

        for level, stats in self.results.items():
            report['by_level'][level] = {
                'total': stats['total'],
                'passed': stats['passed'],
                'failed': stats['failed'],
                'skipped': stats['skipped'],
                'pass_rate': stats['passed'] * 100 / max(stats['total'], 1),
                'errors': stats['errors'],
                'test_details': stats['tests']
            }

        return report

    def save_report(self, filename: str, format: str = 'text'):
        """
        保存报告到文件

        Args:
            filename: 文件名
            format: 格式 ('text' 或 'json')
        """
        if format == 'json':
            report = self.generate_json_report()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            report = self.generate_text_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)


def discover_test_classes(level: str = None, class_filter: str = None) -> List[Tuple[str, type]]:
    """
    发现所有测试类

    Args:
        level: 测试级别过滤 (L1/L2/L3)
        class_filter: 类名过滤器

    Returns:
        测试类列表 [(类名, 类), ...]
    """
    from . import test_l1_basic, test_l1_expression, test_l1_class_function
    from . import test_l2_nested, test_l2_exhaustive
    from . import test_l3_deep, test_l3_combinations

    test_classes = []

    modules_to_load = []
    if level is None or level.upper() == 'L1':
        modules_to_load.append(('L1', test_l1_basic))
    if level is None or level.upper() == 'L1_EXP':
        modules_to_load.append(('L1_EXP', test_l1_expression))
    if level is None or level.upper() == 'L1_CF':
        modules_to_load.append(('L1_CF', test_l1_class_function))
    if level is None or level.upper() == 'L2':
        modules_to_load.append(('L2', test_l2_nested))
    if level is None or level.upper() == 'L2_EX':
        modules_to_load.append(('L2_EX', test_l2_exhaustive))
    if level is None or level.upper() == 'L3':
        modules_to_load.append(('L3', test_l3_deep))
    if level is None or level.upper() == 'L3_CO':
        modules_to_load.append(('L3_CO', test_l3_combinations))

    for level_name, module in modules_to_load:
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                issubclass(obj, ControlFlowTestCase) and
                obj != ControlFlowTestCase):

                # 应用类名过滤器
                if class_filter and class_filter.lower() not in name.lower():
                    continue

                test_classes.append((name, obj, level_name))

    return test_classes


def run_single_test(test_class: type, test_method: str = 'test_structure_correct') -> Tuple[str, str, Optional[str], float]:
    """
    运行单个测试

    Args:
        test_class: 测试类
        test_method: 测试方法名

    Returns:
        (状态, 错误信息, 执行时间)
    """
    start_time = time.time()
    suite = unittest.TestLoader().loadTestsFromName(
        f'{test_class.__name__}.{test_method}',
        module=sys.modules[test_class.__module__]
    )

    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w'), verbosity=0)
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


def main():
    """主函数：解析命令行参数并运行测试"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Python控制流完备性测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                    # 运行所有测试
  python run_tests.py --level L1         # 只运行L1测试
  python run_tests.py --verbose          # 详细输出
  python run_tests.py --format json      # JSON格式输出
  python run_tests.py --output report.txt # 保存报告
  python run_tests.py --class TestB01SimpleAssignment  # 运行特定测试
        """
    )

    parser.add_argument(
        '--level', '-l',
        choices=['L1', 'L1_EXP', 'L1_CF', 'L2', 'L2_EX', 'L3', 'L3_CO'],
        help='只运行指定级别的测试 (L1/L1_EXP/L1_CF/L2/L2_EX/L3/L3_CO)'
    )

    parser.add_argument(
        '--class', '-c',
        dest='class_filter',
        help='只运行名称包含指定字符串的测试类'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (text/json)'
    )

    parser.add_argument(
        '--output', '-o',
        help='保存报告到文件'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='禁用彩色输出'
    )

    args = parser.parse_args()

    # 初始化报告生成器
    reporter = TestReportGenerator()
    reporter.start()

    print("\n" + "=" * 80)
    print("Python 控制流完备性测试框架")
    print("=" * 80)
    print(f"\n正在发现测试用例...")

    # 发现测试类
    try:
        test_classes = discover_test_classes(args.level, args.class_filter)
    except Exception as e:
        print(f"\n错误: 无法加载测试模块 - {e}")
        sys.exit(1)

    if not test_classes:
        print("\n未找到匹配的测试用例")
        sys.exit(0)

    print(f"找到 {len(test_classes)} 个测试用例\n")

    if args.verbose:
        print("-" * 80)
        print("测试详情:")
        print("-" * 80 + "\n")

    # 运行每个测试
    for i, (class_name, test_class, level) in enumerate(test_classes, 1):
        if args.verbose:
            print(f"[{i}/{len(test_classes)}] 运行 {class_name}...", end=" ", flush=True)

        try:
            status, error, duration = run_single_test(test_class)
            reporter.add_result(class_name, level, status, error, duration)

            if args.verbose:
                if status == 'passed':
                    print("✓ 通过" if not args.no_color else "PASS")
                elif status == 'failed':
                    print(f"✗ 失败" if not args.no_color else "FAIL")
                    if error and args.verbose > 1:
                        print(f"  错误: {error[:200]}")
                elif status == 'error':
                    print(f"! 错误" if not args.no_color else "ERROR")
                    if error and args.verbose > 1:
                        print(f"  错误: {error[:200]}")
                else:
                    print("- 跳过" if not args.no_color else "SKIP")

        except Exception as e:
            reporter.add_result(class_name, level, 'error', str(e), 0)
            if args.verbose:
                print(f"! 异常: {e}" if not args.no_color else f"EXCEPTION: {e}")

    reporter.finish()

    # 生成并显示报告
    if args.format == 'json':
        report = reporter.generate_json_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("\n")
        print(reporter.generate_text_report())

    # 保存报告（如果指定）
    if args.output:
        reporter.save_report(args.output, args.format)
        print(f"\n报告已保存到: {args.output}")

    # 返回退出码
    if reporter.total_failed > 0 or reporter.total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
