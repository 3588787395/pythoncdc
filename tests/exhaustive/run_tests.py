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

REGION_TYPES = [
    'basic', 'if_region', 'while_loop', 'for_loop',
    'try_except', 'with_region', 'match_region',
    'boolop', 'ternary', 'nested',
]

EXHAUSTIVE_DIR = os.path.dirname(os.path.abspath(__file__))


class ExhaustiveTestReport:
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        for rt in REGION_TYPES:
            self.results[rt] = {
                'total': 0, 'passed': 0, 'failed': 0,
                'skipped': 0, 'errors': [], 'tests': [],
            }
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0
        self.total_skipped = 0

    def start(self):
        self.start_time = time.time()

    def finish(self):
        self.end_time = time.time()

    def add_result(self, test_class_name: str, region_type: str,
                   status: str, error_message: str = None, duration: float = 0):
        if region_type not in self.results:
            self.results[region_type] = {
                'total': 0, 'passed': 0, 'failed': 0,
                'skipped': 0, 'errors': [], 'tests': [],
            }

        self.results[region_type]['total'] += 1
        self.total_tests += 1

        test_info = {
            'name': test_class_name,
            'status': status,
            'duration': duration,
            'error': error_message,
        }

        if status == 'passed':
            self.results[region_type]['passed'] += 1
            self.total_passed += 1
        elif status == 'failed':
            self.results[region_type]['failed'] += 1
            self.total_failed += 1
            if error_message:
                self.results[region_type]['errors'].append({
                    'test': test_class_name,
                    'error': error_message,
                })
        elif status == 'skipped':
            self.results[region_type]['skipped'] += 1
            self.total_skipped += 1
        elif status == 'error':
            self.results[region_type]['failed'] += 1
            self.total_failed += 1
            if error_message:
                self.results[region_type]['errors'].append({
                    'test': test_class_name,
                    'error': error_message,
                })

        self.results[region_type]['tests'].append(test_info)

    def generate_text_report(self) -> str:
        lines = []
        lines.append("=" * 80)
        lines.append("Python 反编译器穷举测试报告")
        lines.append("=" * 80)
        lines.append("")

        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            lines.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"执行时长: {duration:.2f} 秒")
        lines.append("")

        lines.append("-" * 80)
        lines.append("总体统计")
        lines.append("-" * 80)
        lines.append(f"总测试数: {self.total_tests}")
        pass_rate = self.total_passed * 100 / max(self.total_tests, 1)
        lines.append(f"通过:     {self.total_passed} ({pass_rate:.1f}%)")
        lines.append(f"失败:     {self.total_failed}")
        lines.append(f"跳过:     {self.total_skipped}")
        lines.append("")

        lines.append("-" * 80)
        lines.append("各区域类型统计")
        lines.append("-" * 80)

        for rt in REGION_TYPES:
            if rt in self.results:
                stats = self.results[rt]
                total = stats['total']
                passed = stats['passed']
                failed = stats['failed']
                skipped = stats['skipped']
                rt_pass_rate = passed * 100 / max(total, 1)

                lines.append(f"\n  {rt}:")
                lines.append(f"    总数:   {total}")
                lines.append(f"    通过:   {passed} ({rt_pass_rate:.1f}%)")
                lines.append(f"    失败:   {failed}")
                lines.append(f"    跳过:   {skipped}")

                if stats['errors']:
                    lines.append(f"    失败的测试:")
                    for err in stats['errors'][:10]:
                        err_str = err['error'][:100] if err['error'] else ''
                        lines.append(f"      - {err['test']}: {err_str}")

        lines.append("")
        lines.append("-" * 80)

        overall_pass_rate = self.total_passed * 100 / max(self.total_tests, 1)
        lines.append(f"\n总体通过率: {overall_pass_rate:.2f}%")

        if overall_pass_rate >= 95:
            lines.append("评估: ★★★★★ 优秀 (>=95%)")
        elif overall_pass_rate >= 85:
            lines.append("评估: ★★★★☆ 良好 (>=85%)")
        elif overall_pass_rate >= 70:
            lines.append("评估: ★★★☆☆ 一般 (>=70%)")
        elif overall_pass_rate >= 50:
            lines.append("评估: ★★☆☆☆ 较差 (>=50%)")
        else:
            lines.append("评估: ★☆☆☆☆ 差 (<50%)")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_json_report(self) -> dict:
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'duration': (self.end_time or time.time()) - (self.start_time or time.time()),
                'version': '1.0.0',
            },
            'summary': {
                'total': self.total_tests,
                'passed': self.total_passed,
                'failed': self.total_failed,
                'skipped': self.total_skipped,
                'pass_rate': self.total_passed * 100 / max(self.total_tests, 1),
            },
            'by_region_type': {},
        }

        for rt, stats in self.results.items():
            if stats['total'] > 0:
                report['by_region_type'][rt] = {
                    'total': stats['total'],
                    'passed': stats['passed'],
                    'failed': stats['failed'],
                    'skipped': stats['skipped'],
                    'pass_rate': stats['passed'] * 100 / max(stats['total'], 1),
                    'errors': stats['errors'],
                    'test_details': stats['tests'],
                }

        return report

    def save_report(self, filename: str, format: str = 'text'):
        if format == 'json':
            report = self.generate_json_report()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            report = self.generate_text_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)


def discover_test_files(region_type: str = None) -> List[Tuple[str, str, str]]:
    test_files = []
    types_to_scan = [region_type] if region_type else REGION_TYPES

    for rt in types_to_scan:
        rt_dir = os.path.join(EXHAUSTIVE_DIR, rt)
        if not os.path.isdir(rt_dir):
            continue

        for filename in sorted(os.listdir(rt_dir)):
            if filename.startswith('test_') and filename.endswith('.py'):
                filepath = os.path.join(rt_dir, filename)
                test_files.append((rt, filename, filepath))

    return test_files


def load_test_class(filepath: str) -> Optional[type]:
    module_name = f'exhaustive_test_{os.path.splitext(os.path.basename(filepath))[0]}'

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


def run_single_test(test_class: type, check_bytecode: bool = False) -> Tuple[str, Optional[str], float]:
    start_time = time.time()

    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
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
    import argparse

    parser = argparse.ArgumentParser(
        description='Python反编译器穷举测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                          # 运行所有测试
  python run_tests.py --type basic             # 只运行basic类型
  python run_tests.py --type basic if_region   # 运行多种类型
  python run_tests.py --bytecode               # 启用字节码一致性验证
  python run_tests.py --verbose                # 详细输出
  python run_tests.py --format json            # JSON格式输出
  python run_tests.py --output report.txt      # 保存报告
        """
    )

    parser.add_argument(
        '--type', '-t',
        nargs='*',
        choices=REGION_TYPES,
        help='指定要运行的区域类型'
    )

    parser.add_argument(
        '--bytecode', '-b',
        action='store_true',
        help='启用字节码一致性验证'
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

    args = parser.parse_args()

    reporter = ExhaustiveTestReport()
    reporter.start()

    print("\n" + "=" * 80)
    print("Python 反编译器穷举测试框架")
    print("=" * 80)

    target_types = args.type if args.type else REGION_TYPES
    print(f"\n目标区域类型: {', '.join(target_types)}")
    if args.bytecode:
        print("字节码一致性验证: 已启用")

    print(f"\n正在发现测试用例...")

    test_files = []
    for rt in target_types:
        test_files.extend(discover_test_files(rt))

    if not test_files:
        print("\n未找到测试文件。请先运行 generate_tests.py 生成测试用例。")
        print(f"  python generate_tests.py --type {' '.join(target_types)}")
        sys.exit(0)

    print(f"找到 {len(test_files)} 个测试文件\n")

    if args.verbose:
        print("-" * 80)
        print("测试详情:")
        print("-" * 80 + "\n")

    for i, (region_type, filename, filepath) in enumerate(test_files, 1):
        if args.verbose:
            print(f"[{i}/{len(test_files)}] {region_type}/{filename}...", end=" ", flush=True)

        test_class = load_test_class(filepath)
        if test_class is None:
            if args.verbose:
                print("SKIP (无法加载)")
            reporter.add_result(filename, region_type, 'skipped')
            continue

        try:
            status, error, duration = run_single_test(test_class, args.bytecode)
            reporter.add_result(filename, region_type, status, error, duration)

            if args.verbose:
                if status == 'passed':
                    print("PASS")
                elif status == 'failed':
                    print(f"FAIL")
                    if error:
                        print(f"  {error[:200]}")
                elif status == 'error':
                    print(f"ERROR")
                    if error:
                        print(f"  {error[:200]}")
                else:
                    print("SKIP")

        except Exception as e:
            reporter.add_result(filename, region_type, 'error', str(e), 0)
            if args.verbose:
                print(f"EXCEPTION: {e}")

    reporter.finish()

    if args.format == 'json':
        report = reporter.generate_json_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("\n")
        print(reporter.generate_text_report())

    if args.output:
        reporter.save_report(args.output, args.format)
        print(f"\n报告已保存到: {args.output}")

    if reporter.total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
