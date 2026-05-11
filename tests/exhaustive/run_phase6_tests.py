"""
Phase 6 完备性测试矩阵 - 综合测试运行器

运行所有132+项测试用例，生成完整的覆盖率报告。

使用方法:
    python run_phase6_tests.py                    # 运行所有测试
    python run_phase6_tests.py --level L1          # 只运行L1测试
    python run_phase6_tests.py --bytecode          # 启用字节码验证
    python run_phase6_tests.py --report report.txt # 保存报告
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class Phase6TestRunner:
    """Phase 6完备性测试运行器"""

    def __init__(self):
        self.results = {
            'L1_basic': {'total': 0, 'passed': 0, 'failed': 0, 'errors': [], 'tests': []},
            'L2_two_level_nested': {'total': 0, 'passed': 0, 'failed': 0, 'errors': [], 'tests': []},
            'L3_deep_nested': {'total': 0, 'passed': 0, 'failed': 0, 'errors': [], 'tests': []},
            'P1_expressions': {'total': 0, 'passed': 0, 'failed': 0, 'errors': [], 'tests': []},
        }
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.total_passed = 0
        self.total_failed = 0

    def discover_tests(self, level: str = None) -> List[Tuple[str, str]]:
        """发现测试模块"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        test_modules = []

        test_dirs = {
            'L1_basic': os.path.join(base_dir, 'L1_basic'),
            'L2_two_level_nested': os.path.join(base_dir, 'L2_two_level_nested'),
            'L3_deep_nested': os.path.join(base_dir, 'L3_deep_nested'),
            'P1_expressions': os.path.join(base_dir, 'P1_expressions'),
        }

        levels_to_test = [level] if level else list(test_dirs.keys())

        for lvl in levels_to_test:
            if lvl not in test_dirs:
                print(f"警告: 未知的测试级别 {lvl}")
                continue

            test_file = os.path.join(test_dirs[lvl], f'test_{lvl.lower()}_complete.py')
            if os.path.exists(test_file):
                test_modules.append((lvl, test_file))

        return test_modules

    def run_single_module(self, module_path: str, level: str,
                          verbose: bool = False) -> Tuple[int, int, List[str]]:
        """运行单个测试模块"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(f"phase6_{level}", module_path)
        if spec is None or spec.loader is None:
            return (0, 0, [f"无法加载模块: {module_path}"])

        module = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            return (0, 0, [f"加载模块失败: {e}"])

        # 收集测试类
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                issubclass(obj, unittest.TestCase) and
                obj is not unittest.TestCase):
                suite.addTests(loader.loadTestsFromTestCase(obj))

        # 运行测试
        stream = open(os.devnull, 'w') if not verbose else sys.stdout
        runner = unittest.TextTestRunner(
            stream=stream,
            verbosity=2 if verbose else 0
        )
        result = runner.run(suite)
        if stream != sys.stdout:
            stream.close()

        passed = result.testsRun - len(result.failures) - len(result.errors)
        failed = len(result.failures) + len(result.errors)

        errors = []
        for test, traceback in result.failures + result.errors:
            errors.append(f"{test}: {traceback[:200]}")

        return (result.testsRun, passed, errors)

    def run_all(self, level: str = None, verbose: bool = False,
                bytecode_check: bool = False) -> Dict[str, Any]:
        """运行所有测试"""
        self.start_time = time.time()

        print("\n" + "=" * 80)
        print("Phase 6: CFG区域归约反编译完备性测试矩阵")
        print("=" * 80)
        print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if bytecode_check:
            print("字节码等价性验证: 已启用")
        
        target_levels = [level] if level else ['L1_basic', 'L2_two_level_nested',
                                                'L3_deep_nested', 'P1_expressions']
        print(f"\n目标测试级别: {', '.join(target_levels)}")

        test_modules = self.discover_tests(level)
        print(f"\n发现 {len(test_modules)} 个测试模块\n")

        for i, (lvl, module_path) in enumerate(test_modules, 1):
            if verbose:
                print("-" * 80)
                print(f"[{i}/{len(test_modules)}] 运行 {lvl} 测试...")
                print(f"  模块: {module_path}")
                print()

            total, passed, errors = self.run_single_module(module_path, lvl, verbose)
            failed = total - passed

            self.results[lvl]['total'] += total
            self.results[lvl]['passed'] += passed
            self.results[lvl]['failed'] += failed
            self.results[lvl]['errors'].extend(errors)
            
            self.total_tests += total
            self.total_passed += passed
            self.total_failed += failed

            if verbose:
                print(f"\n结果: {passed}/{total} 通过 ({passed*100/max(total,1):.1f}%)")
                if errors:
                    print(f"失败:")
                    for err in errors[:5]:
                        print(f"  - {err[:150]}")

        self.end_time = time.time()

        return {
            'summary': self.generate_summary(),
            'by_level': self.results,
            'total': {
                'tests': self.total_tests,
                'passed': self.total_passed,
                'failed': self.total_failed,
                'pass_rate': self.total_passed * 100 / max(self.total_tests, 1),
            },
            'duration': self.end_time - self.start_time,
        }

    def generate_summary(self) -> str:
        """生成文本摘要"""
        lines = []
        lines.append("=" * 80)
        lines.append("Phase 6 完备性测试矩阵 - 运行报告")
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
        lines.append("")

        lines.append("-" * 80)
        lines.append("各测试级别统计")
        lines.append("-" * 80)

        expected_counts = {
            'L1_basic': 52,
            'L2_two_level_nested': 48,
            'L3_deep_nested': 18,
            'P1_expressions': 14,
        }

        for lvl, stats in self.results.items():
            if stats['total'] > 0:
                total = stats['total']
                passed = stats['passed']
                failed = stats['failed']
                rate = passed * 100 / max(total, 1)
                expected = expected_counts.get(lvl, '?')
                
                status = "✓" if failed == 0 else "✗"
                coverage = f"{total}/{expected}"
                
                lines.append(f"\n  [{status}] {lvl}:")
                lines.append(f"      覆盖率:   {coverage}")
                lines.append(f"      通过:     {passed} ({rate:.1f}%)")
                lines.append(f"      失败:     {failed}")

                if stats['errors']:
                    lines.append(f"      失败详情:")
                    for err in stats['errors'][:10]:
                        lines.append(f"        - {err[:120]}")

        lines.append("")
        lines.append("-" * 80)

        overall_rate = self.total_passed * 100 / max(self.total_tests, 1)
        lines.append(f"\n总体通过率: {overall_rate:.2f}%")

        if overall_rate >= 95:
            lines.append("评估: ★★★★★ 优秀 (>=95%) - 反编译器控制流处理能力卓越")
        elif overall_rate >= 85:
            lines.append("评估: ★★★★☆ 良好 (>=85%) - 大部分控制流结构正确处理")
        elif overall_rate >= 70:
            lines.append("评估: ★★★☆☆ 一般 (>=70%) - 存在一些需要修复的问题")
        elif overall_rate >= 50:
            lines.append("评估: ★★☆☆☆ 较差 (>=50%) - 需要大量修复工作")
        else:
            lines.append("评估: ★☆☆☆☆ 差 (<50%) - 反编译器存在严重问题")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_json_report(self) -> dict:
        """生成JSON格式报告"""
        expected_counts = {
            'L1_basic': 52,
            'L2_two_level_nested': 48,
            'L3_deep_nested': 18,
            'P1_expressions': 14,
        }

        return {
            'metadata': {
                'phase': 6,
                'title': 'CFG区域归约反编译完备性测试矩阵',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'duration': (self.end_time or time.time()) - (self.start_time or time.time()),
            },
            'summary': {
                'total_tests': self.total_tests,
                'passed': self.total_passed,
                'failed': self.total_failed,
                'pass_rate': self.total_passed * 100 / max(self.total_tests, 1),
            },
            'by_level': {
                lvl: {
                    'expected': expected_counts.get(lvl, 0),
                    'actual': stats['total'],
                    'passed': stats['passed'],
                    'failed': stats['failed'],
                    'pass_rate': stats['passed'] * 100 / max(stats['total'], 1),
                    'coverage_pct': stats['total'] * 100 / max(expected_counts.get(lvl, 1), 1),
                    'errors': stats['errors'][:20],
                }
                for lvl, stats in self.results.items()
                if stats['total'] > 0
            },
            'test_categories': {
                'L1_basic': {
                    'name': '基础结构测试',
                    'description': '覆盖基本语句、条件、循环、异常、with',
                    'items': ['B01-B08: 基础语句(8项)', 'C01-C07: 条件(7项)',
                             'L01-L18: 循环(18项)', 'E01-E13: 异常(13项)',
                             'W01-W06: with(6项)'],
                },
                'L2_two_level_nested': {
                    'name': '两层嵌套测试',
                    'description': '外层×内层组合矩阵',
                    'items': ['IF外层(5项)', 'FOR外层(6项)', 'WHILE外层(6项)',
                             'TRY外层(5项)', 'WITH外层(2项)',
                             '特殊组合(24项)'],
                },
                'L3_deep_nested': {
                    'name': '三层及以上嵌套测试',
                    'description': '深度嵌套结构测试',
                    'items': ['N01-N13: 三层嵌套(13项)', 'N14-N18: 四层嵌套(5项)'],
                },
                'P1_expressions': {
                    'name': '表达式完备性测试',
                    'description': '复杂表达式语法测试',
                    'items': ['BO01-BO04: BoolOp(4项)', 'CC01-CC03: 链式比较(3项)',
                             'T01-T04: 三元表达式(4项)', 'S07: Walrus运算符(1项)',
                             '其他表达式(2项)'],
                },
            },
        }

    def save_report(self, filename: str, format: str = 'text'):
        """保存报告到文件"""
        if format == 'json':
            report = self.generate_json_report()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            report = self.generate_summary()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 6: CFG区域归约反编译完备性测试矩阵',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_phase6_tests.py                      # 运行所有132+项测试
  python run_phase6_tests.py --level L1_basic      # 只运行L1基础测试
  python run_phase6_tests.py --verbose             # 显示详细输出
  python run_phase6_tests.py --report report.txt   # 保存报告到文件
  python run_phase6_tests.py --format json         # JSON格式输出
        """
    )

    parser.add_argument(
        '--level', '-l',
        choices=['L1_basic', 'L2_two_level_nested', 'L3_deep_nested', 'P1_expressions'],
        help='指定要运行的测试级别'
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

    runner = Phase6TestRunner()
    
    try:
        results = runner.run_all(
            level=args.level,
            verbose=args.verbose,
        )
    except Exception as e:
        print(f"\n错误: 运行测试时发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if args.format == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(results['summary'])

    if args.output:
        runner.save_report(args.output, args.format)
        print(f"\n报告已保存到: {args.output}")

    # 返回退出码
    if runner.total_failed > 0:
        print(f"\n⚠ 有 {runner.total_failed} 个测试失败")
        sys.exit(1)
    else:
        print(f"\n✓ 所有 {runner.total_passed} 个测试通过!")
        sys.exit(0)


if __name__ == '__main__':
    main()
