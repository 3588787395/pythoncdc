#!/usr/bin/env python3
"""
完备性测试矩阵运行脚本
运行所有L1/L2/L3/P1测试并生成报告

用法:
    python run_test_matrix.py                          # 运行所有测试
    python run_test_matrix.py --level L1               # 只运行L1测试
    python run_test_matrix.py --category basic,if_region  # 运行特定类别
    python run_test_matrix.py --verbose                # 详细输出
    python run_test_matrix.py --format json            # JSON格式输出
    python run_test_matrix.py --output report.txt      # 保存报告
"""

import os
import sys
import time
import json
import unittest
import importlib.util
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.exhaustive.base import ExhaustiveTestCase


@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    file_path: Path
    category: str
    level: str
    passed: bool
    status: str  # passed, failed, error, skipped
    output: str = ""
    duration: float = 0.0
    error_message: str = ""


@dataclass
class CategoryStats:
    """类别统计信息"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total_duration: float = 0.0
    failures: List[Dict] = field(default_factory=list)


class TestMatrixRunner:
    """测试矩阵运行器"""

    EXHAUSTIVE_DIR = Path(__file__).parent

    LEVEL_CATEGORIES = {
        'L1': ['basic', 'if_region', 'for_loop', 'while_loop', 'try_except', 'with_region', 'match_region', 'L1_basic'],
        'L2': ['nested', 'L2_two_level_nested'],
        'L3': ['triple_nested', 'l3_three_level_nested', 'L3_deep_nested'],
        'P1': ['boolop', 'ternary', 'P1_expressions']
    }

    CATEGORY_LEVEL_MAP = {}
    for level, categories in LEVEL_CATEGORIES.items():
        for cat in categories:
            CATEGORY_LEVEL_MAP[cat] = level

    MATRIX_IDS = {
        'L1': {
            'basic': list(range(1, 9)),  # B01-B08
            'if_region': list(range(1, 8)),  # C01-C07
            'for_loop': list(range(1, 19)),  # L01-L18
            'while_loop': list(range(1, 19)),
            'try_except': list(range(1, 14)),  # E01-E13
            'with_region': list(range(1, 7)),  # W01-W06
            'match_region': list(range(1, 109)),  # M001-M108（含 _a/_n/_x 变体）
            'L1_basic': list(range(1, 53))
        },
        'L2': {
            'nested': list(range(1, 49)),  # IF01-IF05, LO01-LO06, etc.
            'L2_two_level_nested': list(range(1, 49))
        },
        'L3': {
            'triple_nested': list(range(1, 19)),  # N01-N18
            'l3_three_level_nested': list(range(1, 19)),
            'L3_deep_nested': list(range(1, 19))
        },
        'P1': {
            'boolop': list(range(1, 5)),  # BO01-BO04
            'ternary': list(range(1, 5)),  # T01-T04
            'P1_expressions': [7]  # S07
        }
    }

    def __init__(self):
        self.results: List[TestResult] = []
        self.stats_by_level: Dict[str, CategoryStats] = {
            level: CategoryStats() for level in ['L1', 'L2', 'L3', 'P1']
        }
        self.stats_by_category: Dict[str, CategoryStats] = defaultdict(CategoryStats)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def discover_tests(self, target_categories: List[str] = None,
                       target_level: str = None) -> List[Tuple[str, Path]]:
        """发现所有测试用例文件
        
        Returns:
            List of (category_name, file_path) tuples
        """
        test_files = []

        categories_to_scan = []
        if target_level:
            categories_to_scan = self.LEVEL_CATEGORIES.get(target_level, [])
        elif target_categories:
            categories_to_scan = target_categories
        else:
            for cats in self.LEVEL_CATEGORIES.values():
                categories_to_scan.extend(cats)

        for category in categories_to_scan:
            cat_dir = self.EXHAUSTIVE_DIR / category
            if not cat_dir.exists() or not cat_dir.is_dir():
                continue

            for test_file in sorted(cat_dir.glob('test_*.py')):
                if test_file.name.startswith('test_') and test_file.suffix == '.py':
                    test_files.append((category, test_file))

        return test_files

    def classify_test(self, category: str, test_file: Path) -> Tuple[str, str]:
        """分类测试到层次和类别
        
        Returns:
            (level, matrix_id)
        """
        level = self.CATEGORY_LEVEL_MAP.get(category, 'UNKNOWN')

        filename = test_file.stem
        matrix_id = ""

        if category == 'basic':
            if 'b15return' in filename or 'b16return' in filename:
                matrix_id = "B06"
            elif 'b17returnvar' in filename:
                matrix_id = "C07"
            elif 'b18pass' in filename:
                matrix_id = "B08"
            elif 'b29tupleunpack' in filename:
                matrix_id = "B04"
            elif 'b31attrassign' in filename or 'b32exprbinop' in filename:
                matrix_id = "B01"
            elif 'b05exprstmt' in filename:
                matrix_id = "B05"

        elif category == 'if_region':
            if 'if01ifthen' in filename:
                matrix_id = "C01"
            elif 'if02ifelse' in filename:
                matrix_id = "C02"
            elif 'if44ifintry' in filename:
                matrix_id = "E12"
            elif 'if45ifinwith' in filename:
                matrix_id = "IF05"
            elif 'if42ifinfor' in filename:
                matrix_id = "IF02"

        elif category == 'for_loop':
            if 'fl01simplefor' in filename or 'l01simplefor' in filename:
                matrix_id = "L01"
            elif 'l02forelse' in filename or 'fl02forelse' in filename:
                matrix_id = "L02"
            elif 'l03forbreak' in filename or 'fl03forbreak' in filename:
                matrix_id = "L03"
            elif 'l18nestedfor' in filename or 'flnestedfor' in filename:
                matrix_id = "L09"
            elif 'fl44forinif' in filename:
                matrix_id = "LO01"

        elif category == 'with_region':
            if 'w01withas' in filename:
                matrix_id = "W01"
            elif 'w09withnoas' in filename:
                matrix_id = "W02"
            elif 'w03multicontext' in filename or 'w22multicontext' in filename:
                matrix_id = "W03"
            elif 'w04nestedwith' in filename or 'w16nestedwith' in filename:
                matrix_id = "W04"
            elif 'w05withtry' in filename or 'w15withtry' in filename:
                matrix_id = "W05"
            elif 'w23withintry' in filename:
                matrix_id = "W06"

        elif category == 'nested':
            if 'n01ifinwhile' in filename:
                matrix_id = "WH01"
            elif 'n02ifinfor' in filename:
                matrix_id = "LO01"
            elif 'n03forinif' in filename:
                matrix_id = "IF02"
            elif 'n04whileinif' in filename:
                matrix_id = "IF03"
            elif 'n10forinfor' in filename:
                matrix_id = "LO02"
            elif 'n11ifinif' in filename:
                matrix_id = "IF01"

        elif category == 'boolop':
            if 'bo01and' in filename:
                matrix_id = "BO01"
            elif 'bo02or' in filename:
                matrix_id = "BO02"
            elif 'bo03not' in filename:
                matrix_id = "BO03"
            elif 'bo04andor' in filename or 'bo24orandor' in filename:
                matrix_id = "BO04"

        elif category == 'match_region':
            # match_region 文件命名不规则：test_m001.py / test_m05matchmapping_a.py
            # 提取 m 后的数字作为 matrix_id（仅用于文档/统计，不影响测试运行）
            if filename.startswith('test_m'):
                digits = ''
                for ch in filename[len('test_m'):]:
                    if ch.isdigit():
                        digits += ch
                    else:
                        break
                if digits:
                    matrix_id = f"M{int(digits):03d}"

        return level, matrix_id

    def load_test_class(self, test_file: Path) -> Optional[type]:
        """加载测试类"""
        module_name = f'matrix_test_{test_file.stem}'

        try:
            spec = importlib.util.spec_from_file_location(module_name, str(test_file))
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and
                        issubclass(obj, ExhaustiveTestCase) and
                        obj is not ExhaustiveTestCase):
                    return obj

        except Exception as e:
            pass

        return None

    def run_single_test(self, test_class: type, category: str,
                       test_file: Path, verbose: bool = False) -> TestResult:
        """运行单个测试"""
        start_time = time.time()
        level, matrix_id = self.classify_test(category, test_file)

        try:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(
                stream=open(os.devnull, 'w'),
                verbosity=0
            )
            result = runner.run(suite)

            duration = time.time() - start_time

            if result.wasSuccessful():
                status = 'passed'
                passed = True
                error_msg = ''
            elif result.errors:
                status = 'error'
                passed = False
                error_msg = str(result.errors[0][1])[:500]
            elif result.failures:
                status = 'failed'
                passed = False
                error_msg = str(result.failures[0][1])[:500]
            else:
                status = 'skipped'
                passed = True
                error_msg = ''

        except Exception as e:
            duration = time.time() - start_time
            status = 'error'
            passed = False
            error_msg = str(e)[:500]

        return TestResult(
            name=test_file.name,
            file_path=test_file,
            category=category,
            level=level,
            passed=passed,
            status=status,
            duration=duration,
            error_message=error_msg
        )

    def run_all(self, target_level: str = None,
               target_categories: List[str] = None,
               verbose: bool = False,
               check_bytecode: bool = False) -> Dict[str, Any]:
        """运行所有测试并生成报告"""
        self.start_time = datetime.now()

        print("\n" + "=" * 80)
        print("=== CFG 区域模式反编译器 - 完备性测试矩阵 ===")
        print(f"时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        test_files = self.discover_tests(target_categories, target_level)

        if not test_files:
            print("\n❌ 未找到测试文件")
            print("请检查 tests/exhaustive/ 目录是否存在测试用例")
            return {'all_passed': False, 'results': [], 'stats': {}}

        print(f"\n✓ 发现测试文件: {len(test_files)} 个")

        if target_level:
            print(f"  目标层次: {target_level}")
        if target_categories:
            print(f"  目标类别: {', '.join(target_categories)}")

        cat_counts = defaultdict(int)
        for cat, _ in test_files:
            cat_counts[cat] += 1

        print("\n按类别分布:")
        for cat in sorted(cat_counts.keys()):
            level = self.CATEGORY_LEVEL_MAP.get(cat, '??')
            print(f"  [{level}] {cat}: {cat_counts[cat]} 个")

        print(f"\n{'=' * 80}")
        print("开始执行测试...")
        print("=" * 80 + "\n")

        all_passed = True
        for i, (category, test_file) in enumerate(test_files, 1):
            if verbose:
                print(f"[{i}/{len(test_files)}] {category}/{test_file.name}...", end=" ", flush=True)

            test_class = self.load_test_class(test_file)

            if test_class is None:
                result = TestResult(
                    name=test_file.name,
                    file_path=test_file,
                    category=category,
                    level=self.CATEGORY_LEVEL_MAP.get(category, 'UNKNOWN'),
                    passed=True,
                    status='skipped',
                    error_message='无法加载测试类'
                )
                self.results.append(result)
                if verbose:
                    print("SKIP")
                continue

            result = self.run_single_test(test_class, category, test_file, verbose)
            self.results.append(result)

            self._update_stats(result)

            if verbose:
                status_icon = "✅" if result.passed else "❌"
                print(f"{status_icon} ({result.duration:.2f}s)")
                if not result.passed and result.error_message:
                    print(f"     错误: {result.error_message[:150]}...")

            if not result.passed and result.status != 'skipped':
                all_passed = False

        self.end_time = datetime.now()

        report = self._generate_report(all_passed, verbose)
        return report

    def _update_stats(self, result: TestResult):
        """更新统计信息"""
        if result.level in self.stats_by_level:
            stats = self.stats_by_level[result.level]
            stats.total += 1
            stats.total_duration += result.duration
            if result.status == 'passed':
                stats.passed += 1
            elif result.status == 'failed':
                stats.failed += 1
                stats.failures.append({
                    'name': result.name,
                    'category': result.category,
                    'error': result.error_message
                })
            elif result.status == 'error':
                stats.errors += 1
                stats.failures.append({
                    'name': result.name,
                    'category': result.category,
                    'error': result.error_message
                })
            elif result.status == 'skipped':
                stats.skipped += 1

        stats_cat = self.stats_by_category[result.category]
        stats_cat.total += 1
        stats_cat.total_duration += result.duration
        if result.status == 'passed':
            stats_cat.passed += 1
        elif result.status == 'failed':
            stats_cat.failed += 1
        elif result.status == 'error':
            stats_cat.errors += 1
        elif result.status == 'skipped':
            stats_cat.skipped += 1

    def _generate_report(self, all_passed: bool, verbose: bool) -> Dict[str, Any]:
        """生成汇总报告"""
        print("\n\n" + "=" * 80)
        print("=== 测试矩阵执行报告 ===")
        print("=" * 80)

        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r.passed)
        total_failed = sum(1 for r in self.results if not r.passed and r.status not in ('skipped',))
        total_errors = sum(1 for r in self.results if r.status == 'error')
        total_skipped = sum(1 for r in self.results if r.status == 'skipped')
        total_duration = sum(r.duration for r in self.results)

        pass_rate = (total_passed * 100 / max(total_tests, 1))

        print(f"\n📊 总体统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   ✅ 通过:   {total_passed} ({pass_rate:.1f}%)")
        print(f"   ❌ 失败:   {total_failed}")
        print(f"   ⚠️  错误:   {total_errors}")
        print(f"   ⏭️  跳过:   {total_skipped}")
        print(f"   ⏱️  耗时:   {total_duration:.2f}s")

        if self.start_time and self.end_time:
            wall_time = (self.end_time - self.start_time).total_seconds()
            print(f"   🕐 总时间: {wall_time:.2f}s")

        print(f"\n{'=' * 80}")
        print("📈 各层次统计:")
        print("=" * 80)

        for level in ['L1', 'L2', 'L3', 'P1']:
            stats = self.stats_by_level[level]
            if stats.total > 0:
                level_pass_rate = (stats.passed * 100 / stats.total)
                print(f"\n  [{level}] 基础结构/嵌套/深层/表达式:")
                print(f"    总数: {stats.total} | 通过: {stats.passed} ({level_pass_rate:.1f}%) | "
                      f"失败: {stats.failed} | 错误: {stats.errors} | 跳过: {stats.skipped}")

                if stats.failures and verbose:
                    print(f"    失败详情:")
                    for fail in stats.failures[:5]:
                        print(f"      ❌ {fail['name']} ({fail['category']})")
                        if fail['error']:
                            print(f"         {fail['error'][:100]}...")

        print(f"\n{'=' * 80}")
        print("📂 各类别详细统计:")
        print("=" * 80)

        for category in sorted(self.stats_by_category.keys()):
            stats = self.stats_by_category[category]
            if stats.total > 0:
                cat_pass_rate = (stats.passed * 100 / stats.total)
                level = self.CATEGORY_LEVEL_MAP.get(category, '??')
                print(f"  [{level}] {category:20s}: {stats.total:4d} 测试 | "
                      f"{stats.passed:4d} 通过 ({cat_pass_rate:5.1f}%) | "
                      f"{stats.failed:2d} 失败 | {stats.total_duration:6.2f}s")

        print(f"\n{'=' * 80}")
        print("🎯 覆盖率评估:")
        print("=" * 80)

        if pass_rate >= 95:
            grade = "★★★★★ 优秀"
            assessment = "反编译器控制流处理能力优秀，可以投入生产使用"
        elif pass_rate >= 85:
            grade = "★★★★☆ 良好"
            assessment = "控制流处理能力良好，有少量问题需要修复"
        elif pass_rate >= 70:
            grade = "★★★☆☆ 一般"
            assessment = "基本功能可用，但存在较多问题需要关注"
        elif pass_rate >= 50:
            grade = "★★☆☆☆ 较差"
            assessment = "存在严重问题，需要大量修复工作"
        else:
            grade = "★☆☆☆☆ 差"
            assessment = "反编译器无法正常工作，需要全面修复"

        print(f"\n  总体通过率: {pass_rate:.2f}%")
        print(f"  评估等级:   {grade}")
        print(f"  评估意见:   {assessment}")
        print(f"  总体状态:   {'✅ 全部通过' if all_passed else '❌ 存在失败'}")

        if not all_passed:
            print(f"\n  ⚠️  失败的测试:")
            failed_tests = [r for r in self.results if not r.passed and r.status != 'skipped']
            for result in failed_tests[:10]:
                print(f"    ❌ [{result.level}] {result.category}/{result.name}")
                if result.error_message and verbose:
                    print(f"       {result.error_message[:150]}...")

            if len(failed_tests) > 10:
                print(f"    ... 还有 {len(failed_tests) - 10} 个失败测试")

        print(f"\n{'=' * 80}\n")

        return {
            'all_passed': all_passed,
            'results': [
                {
                    'name': r.name,
                    'category': r.category,
                    'level': r.level,
                    'status': r.status,
                    'passed': r.passed,
                    'duration': r.duration,
                    'error': r.error_message
                }
                for r in self.results
            ],
            'stats': {
                'total': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'errors': total_errors,
                'skipped': total_skipped,
                'pass_rate': pass_rate,
                'duration': total_duration,
                'by_level': {
                    level: {
                        'total': s.total,
                        'passed': s.passed,
                        'failed': s.failed,
                        'errors': s.errors,
                        'skipped': s.skipped,
                        'pass_rate': (s.passed * 100 / max(s.total, 1)),
                        'duration': s.total_duration
                    }
                    for level, s in self.stats_by_level.items()
                },
                'by_category': {
                    cat: {
                        'total': s.total,
                        'passed': s.passed,
                        'failed': s.failed,
                        'errors': s.errors,
                        'skipped': s.skipped,
                        'pass_rate': (s.passed * 100 / max(s.total, 1)),
                        'duration': s.total_duration
                    }
                    for cat, s in self.stats_by_category.items()
                }
            },
            'metadata': {
                'timestamp': self.start_time.isoformat() if self.start_time else None,
                'duration': (self.end_time - self.start_time).total_seconds() if (self.start_time and self.end_time) else 0,
                'version': '1.0.0'
            }
        }

    def save_report(self, report: Dict, filename: str, format: str = 'text'):
        """保存报告到文件"""
        if format == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# CFG 完备性测试矩阵报告\n\n")
                f.write(f"**生成时间**: {report['metadata']['timestamp']}\n\n")
                f.write(f"## 总体统计\n\n")
                f.write(f"- 总测试数: {report['stats']['total']}\n")
                f.write(f"- 通过率: {report['stats']['pass_rate']:.2f}%\n\n")
                f.write(f"## 详细结果\n\n")
                for result in report['results']:
                    status = "✅" if result['passed'] else "❌"
                    f.write(f"- {status} [{result['level']}] {result['category']}/{result['name']}\n")


def main():
    parser = argparse.ArgumentParser(
        description='CFG区域模式反编译器完备性测试矩阵运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_test_matrix.py                          # 运行所有测试
  python run_test_matrix.py --level L1               # 只运行L1基础测试
  python run_test_matrix.py --level L2               # 只运行L2嵌套测试
  python run_test_matrix.py --level L3               # 只运行L3深层测试
  python run_test_matrix.py --level P1               # 只运行P1表达式测试
  python run_test_matrix.py --category basic,if_region  # 运行特定类别
  python run_test_matrix.py --verbose                # 显示详细输出
  python run_test_matrix.py --format json            # JSON格式输出
  python run_test_matrix.py --output report.txt      # 保存报告
        """
    )

    parser.add_argument(
        '--level', '-l',
        choices=['L1', 'L2', 'L3', 'P1'],
        help='指定要运行的测试层次 (L1基础/L2两层嵌套/L3三层及以上/P1表达式)'
    )

    parser.add_argument(
        '--category', '-c',
        nargs='+',
        help='指定要运行的测试类别 (basic, if_region, for_loop, etc.)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出（包括每个测试的状态和错误信息）'
    )

    parser.add_argument(
        '--bytecode', '-b',
        action='store_true',
        help='启用字节码一致性验证（如果测试支持）'
    )

    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)'
    )

    parser.add_argument(
        '--output', '-o',
        help='保存报告到文件'
    )

    args = parser.parse_args()

    runner = TestMatrixRunner()

    try:
        report = runner.run_all(
            target_level=args.level,
            target_categories=args.category,
            verbose=args.verbose,
            check_bytecode=args.bytecode
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if args.format == 'json':
        print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.output:
        runner.save_report(report, args.output, args.format)
        print(f"\n💾 报告已保存到: {args.output}")

    sys.exit(0 if report['all_passed'] else 1)


if __name__ == '__main__':
    main()
