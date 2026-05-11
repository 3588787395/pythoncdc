#!/usr/bin/env python
"""
Phase 6 完备性测试矩阵运行器

运行全部146项测试：
- L1: 52项基础结构测试
- L2: 48项两层嵌套测试
- L3: 18项三层及以上嵌套测试
- P1: 14项表达式完备性测试

总计: 132项测试
"""

import sys
import os
import unittest
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def run_phase6_tests(verbose=False):
    """运行Phase 6全部测试"""

    print("=" * 80)
    print("CFG区域模式反编译器 Phase 6 完备性测试")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # 测试模块列表
    test_modules = [
        # L1基础结构测试 (52项)
        ('L1_basic', 'tests.exhaustive.L1_basic.test_L1_complete', 'L1基础结构测试'),
        # L2两层嵌套测试 (48项)
        ('L2_nested', 'tests.exhaustive.L2_nested.test_L2_complete', 'L2两层嵌套测试'),
        # L3三层及以上嵌套测试 (18项)
        ('L3_deep_nested', 'tests.exhaustive.L3_deep_nested.test_L3_complete', 'L3三层及以上嵌套测试'),
        # P1表达式完备性测试 (14项)
        ('P1_expressions', 'tests.exhaustive.P1_expressions.test_P1_complete', 'P1表达式完备性测试'),
    ]

    total_results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'error': 0,
        'skipped': 0,
    }

    detailed_results = []
    start_time = time.time()

    for module_name, module_path, description in test_modules:
        print(f"\n{'=' * 80}")
        print(f"运行 {description} ({module_name})")
        print('=' * 80)

        try:
            # 动态导入测试模块
            __import__(module_path)
            suite = unittest.TestLoader().loadTestsFromName(module_path)

            # 运行测试
            runner = unittest.TextTestRunner(
                verbosity=2 if verbose else 0,
                stream=open(os.devnull, 'w') if not verbose else sys.stdout
            )
            result = runner.run(suite)

            # 统计结果
            module_total = result.testsRun
            module_passed = module_total - len(result.failures) - len(result.errors) - len(result.skipped)
            module_failed = len(result.failures)
            module_error = len(result.errors)
            module_skipped = len(result.skipped)

            total_results['total'] += module_total
            total_results['passed'] += module_passed
            total_results['failed'] += module_failed
            total_results['error'] += module_error
            total_results['skipped'] += module_skipped

            # 记录详细信息
            detailed_results.append({
                'module': module_name,
                'description': description,
                'total': module_total,
                'passed': module_passed,
                'failed': module_failed,
                'error': module_error,
                'skipped': module_skipped,
                'pass_rate': (module_passed / module_total * 100) if module_total > 0 else 0,
                'failures': [(test.id(), str(traceback)) for test, traceback in result.failures[:5]],
                'errors': [(test.id(), str(traceback)) for test, traceback in result.errors[:5]],
            })

            # 输出摘要
            print(f"\n{description} 结果:")
            print(f"  总计: {module_total}")
            print(f"  通过: {module_passed} ✓")
            if module_failed > 0:
                print(f"  失败: {module_failed} ✗")
            if module_error > 0:
                print(f"  错误: {module_error} !")
            if module_skipped > 0:
                print(f"  跳过: {module_skipped} -")
            pass_rate = (module_passed / module_total * 100) if module_total > 0 else 0
            print(f"  通过率: {pass_rate:.1f}%")

        except Exception as e:
            print(f"\n❌ 加载测试模块失败: {e}")
            import traceback
            traceback.print_exc()
            detailed_results.append({
                'module': module_name,
                'description': description,
                'error': str(e),
                'total': 0,
                'passed': 0,
                'failed': 0,
                'error': 1,
                'skipped': 0,
            })

    end_time = time.time()
    duration = end_time - start_time

    # 输出总体报告
    print("\n")
    print("=" * 80)
    print("📊 Phase 6 完备性测试总体报告")
    print("=" * 80)
    print()
    print(f"总测试数:     {total_results['total']}")
    print(f"通过:         {total_results['passed']} ✓")
    print(f"失败:         {total_results['failed']} ✗")
    print(f"错误:         {total_results['error']} !")
    print(f"跳过:         {total_results['skipped']} -")
    print()

    overall_pass_rate = (total_results['passed'] / total_results['total'] * 100) if total_results['total'] > 0 else 0
    print(f"总体通过率:   {overall_pass_rate:.1f}%")
    print(f"执行时间:     {duration:.2f}秒")
    print()

    # 目标达成情况
    target_rate = 100.0
    if overall_pass_rate >= target_rate:
        print(f"✅ 目标达成! 通过率 {overall_pass_rate:.1f}% >= 目标 {target_rate}%")
    else:
        gap = target_rate - overall_pass_rate
        print(f"❌ 未达目标! 差距 {gap:.1f}% (目标 {target_rate}%)")

    print()

    # 详细结果表格
    print("=" * 80)
    print("📋 各模块详细结果")
    print("=" * 80)
    print(f"{'模块':<20} {'描述':<25} {'总数':>5} {'通过':>5} {'失败':>5} {'错误':>5} {'通过率':>8}")
    print("-" * 80)

    for detail in detailed_results:
        if 'error' in detail and isinstance(detail.get('error'), str):
            print(f"{detail['module']:<20} {detail['description']:<25} {'ERROR':>5} {'-':>5} {'-':>5} {'-':>5} {'N/A':>8}")
        else:
            print(f"{detail['module']:<20} {detail['description']:<25} "
                  f"{detail['total']:>5} {detail['passed']:>5} "
                  f"{detail['failed']:>5} {detail['error']:>5} "
                  f"{detail['pass_rate']:>7.1f}%")

    print("-" * 80)
    print(f"{'总计':<20} {'':<25} {total_results['total']:>5} {total_results['passed']:>5} "
          f"{total_results['failed']:>5} {total_results['error']:>5} {overall_pass_rate:>7.1f}%")
    print()

    # 失败详情（如果有）
    if total_results['failed'] > 0 or total_results['error'] > 0:
        print("=" * 80)
        print("⚠️  失败/错误用例详情")
        print("=" * 80)

        for detail in detailed_results:
            if detail.get('failures'):
                print(f"\n{detail['module']} 失败用例:")
                for test_id, traceback_str in detail['failures'][:10]:
                    print(f"  ❌ {test_id}")
                    if verbose:
                        print(f"     {traceback_str[:200]}...")

            if detail.get('errors'):
                print(f"\n{detail['module']} 错误用例:")
                for test_id, traceback_str in detail['errors'][:10]:
                    print(f"  ! {test_id}")
                    if verbose:
                        print(f"     {traceback_str[:200]}...")

    print()
    print("=" * 80)
    print("测试完成!")
    print("=" * 80)

    return total_results


if __name__ == '__main__':
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    results = run_phase6_tests(verbose=verbose)

    # 返回退出码
    if results['failed'] > 0 or results['error'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
