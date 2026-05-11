#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
控制流测试框架验证脚本

用于：
1. 统计所有测试用例数量
2. 验证所有测试类是否可以正确加载
3. 检查是否有语法错误
4. 生成测试框架摘要
"""

import sys
import os
import ast
import inspect
from typing import Tuple

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def count_test_classes(module):
    """统计模块中的测试类数量"""
    count = 0
    test_classes = []
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and
            hasattr(obj, 'SOURCE_CODE') and
            obj.SOURCE_CODE and
            hasattr(obj, 'test_structure_correct')):
            count += 1
            test_classes.append(name)
    return count, test_classes

def validate_source_code(source_code: str, class_name: str) -> Tuple[bool, str]:
    """验证源代码是否可以编译"""
    try:
        compile(source_code, '<test>', 'exec')
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    print("=" * 80)
    print("Python 控制流完备性测试框架 - 验证报告")
    print("=" * 80)
    print()

    total_tests = 0
    all_valid = True
    summary = {}

    # 测试L1模块
    print("-" * 80)
    print("正在验证 L1 基本结构测试 (test_l1_basic.py)...")
    print("-" * 80)

    try:
        from . import test_l1_basic
        l1_count, l1_classes = count_test_classes(test_l1_basic)
        print(f"✓ 成功加载 L1 模块")
        print(f"  发现 {l1_count} 个测试类")

        # 验证每个测试类的源代码
        l1_valid = 0
        l1_invalid = []
        for class_name in l1_classes:
            test_class = getattr(test_l1_basic, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l1_valid += 1
            else:
                l1_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l1_valid}/{l1_count}")
        if l1_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l1_invalid[:5]:  # 只显示前5个
                print(f"      - {name}: {err[:100]}")

        summary['L1'] = {
            'total': l1_count,
            'valid': l1_valid,
            'classes': l1_classes
        }
        total_tests += l1_count

    except Exception as e:
        print(f"✗ 无法加载 L1 模块: {e}")
        all_valid = False
        summary['L1'] = {'error': str(e)}

    print()

    # 测试L2模块
    print("-" * 80)
    print("正在验证 L2 两层嵌套测试 (test_l2_nested.py)...")
    print("-" * 80)

    try:
        from . import test_l2_nested
        l2_count, l2_classes = count_test_classes(test_l2_nested)
        print(f"✓ 成功加载 L2 模块")
        print(f"  发现 {l2_count} 个测试类")

        l2_valid = 0
        l2_invalid = []
        for class_name in l2_classes:
            test_class = getattr(test_l2_nested, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l2_valid += 1
            else:
                l2_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l2_valid}/{l2_count}")
        if l2_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l2_invalid[:5]:
                print(f"      - {name}: {err[:100]}")

        summary['L2'] = {
            'total': l2_count,
            'valid': l2_valid,
            'classes': l2_classes
        }
        total_tests += l2_count

    except Exception as e:
        print(f"✗ 无法加载 L2 模块: {e}")
        all_valid = False
        summary['L2'] = {'error': str(e)}

    print()

    # 测试L3模块
    print("-" * 80)
    print("正在验证 L3 三层嵌套测试 (test_l3_deep.py)...")
    print("-" * 80)

    try:
        from . import test_l3_deep
        l3_count, l3_classes = count_test_classes(test_l3_deep)
        print(f"✓ 成功加载 L3 模块")
        print(f"  发现 {l3_count} 个测试类")

        l3_valid = 0
        l3_invalid = []
        for class_name in l3_classes:
            test_class = getattr(test_l3_deep, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l3_valid += 1
            else:
                l3_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l3_valid}/{l3_count}")
        if l3_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l3_invalid[:5]:
                print(f"      - {name}: {err[:100]}")

        summary['L3'] = {
            'total': l3_count,
            'valid': l3_valid,
            'classes': l3_classes
        }
        total_tests += l3_count

    except Exception as e:
        print(f"✗ 无法加载 L3 模块: {e}")
        all_valid = False
        summary['L3'] = {'error': str(e)}

    print()

    # 测试L1_EXP模块
    print("-" * 80)
    print("正在验证 L1_EXP 表达式级测试 (test_l1_expression.py)...")
    print("-" * 80)

    try:
        from . import test_l1_expression
        l1e_count, l1e_classes = count_test_classes(test_l1_expression)
        print(f"✓ 成功加载 L1_EXP 模块")
        print(f"  发现 {l1e_count} 个测试类")

        l1e_valid = 0
        l1e_invalid = []
        for class_name in l1e_classes:
            test_class = getattr(test_l1_expression, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l1e_valid += 1
            else:
                l1e_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l1e_valid}/{l1e_count}")
        if l1e_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l1e_invalid[:5]:
                print(f"      - {name}: {err[:100]}")

        summary['L1_EXP'] = {
            'total': l1e_count,
            'valid': l1e_valid,
            'classes': l1e_classes
        }
        total_tests += l1e_count

    except Exception as e:
        print(f"✗ 无法加载 L1_EXP 模块: {e}")
        all_valid = False
        summary['L1_EXP'] = {'error': str(e)}

    print()

    # 测试L1_CF模块
    print("-" * 80)
    print("正在验证 L1_CF 函数/类测试 (test_l1_class_function.py)...")
    print("-" * 80)

    try:
        from . import test_l1_class_function
        l1c_count, l1c_classes = count_test_classes(test_l1_class_function)
        print(f"✓ 成功加载 L1_CF 模块")
        print(f"  发现 {l1c_count} 个测试类")

        l1c_valid = 0
        l1c_invalid = []
        for class_name in l1c_classes:
            test_class = getattr(test_l1_class_function, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l1c_valid += 1
            else:
                l1c_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l1c_valid}/{l1c_count}")
        if l1c_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l1c_invalid[:5]:
                print(f"      - {name}: {err[:100]}")

        summary['L1_CF'] = {
            'total': l1c_count,
            'valid': l1c_valid,
            'classes': l1c_classes
        }
        total_tests += l1c_count

    except Exception as e:
        print(f"✗ 无法加载 L1_CF 模块: {e}")
        all_valid = False
        summary['L1_CF'] = {'error': str(e)}

    print()

    # 测试L2_EX模块
    print("-" * 80)
    print("正在验证 L2_EX 穷举组合测试 (test_l2_exhaustive.py)...")
    print("-" * 80)

    try:
        from . import test_l2_exhaustive
        l2e_count, l2e_classes = count_test_classes(test_l2_exhaustive)
        print(f"✓ 成功加载 L2_EX 模块")
        print(f"  发现 {l2e_count} 个测试类")

        l2e_valid = 0
        l2e_invalid = []
        for class_name in l2e_classes:
            test_class = getattr(test_l2_exhaustive, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l2e_valid += 1
            else:
                l2e_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l2e_valid}/{l2e_count}")
        if l2e_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l2e_invalid[:5]:
                print(f"      - {name}: {err[:100]}")

        summary['L2_EX'] = {
            'total': l2e_count,
            'valid': l2e_valid,
            'classes': l2e_classes
        }
        total_tests += l2e_count

    except Exception as e:
        print(f"✗ 无法加载 L2_EX 模块: {e}")
        all_valid = False
        summary['L2_EX'] = {'error': str(e)}

    print()

    # 测试L3_CO模块
    print("-" * 80)
    print("正在验证 L3_CO 三层组合测试 (test_l3_combinations.py)...")
    print("-" * 80)

    try:
        from . import test_l3_combinations
        l3c_count, l3c_classes = count_test_classes(test_l3_combinations)
        print(f"✓ 成功加载 L3_CO 模块")
        print(f"  发现 {l3c_count} 个测试类")

        l3c_valid = 0
        l3c_invalid = []
        for class_name in l3c_classes:
            test_class = getattr(test_l3_combinations, class_name)
            is_valid, msg = validate_source_code(test_class.SOURCE_CODE, class_name)
            if is_valid:
                l3c_valid += 1
            else:
                l3c_invalid.append((class_name, msg))
                all_valid = False

        print(f"  ✓ 源代码有效: {l3c_valid}/{l3c_count}")
        if l3c_invalid:
            print(f"  ✗ 无效的源代码:")
            for name, err in l3c_invalid[:5]:
                print(f"      - {name}: {err[:100]}")

        summary['L3_CO'] = {
            'total': l3c_count,
            'valid': l3c_valid,
            'classes': l3c_classes
        }
        total_tests += l3c_count

    except Exception as e:
        print(f"✗ 无法加载 L3_CO 模块: {e}")
        all_valid = False
        summary['L3_CO'] = {'error': str(e)}

    print()
    print("=" * 80)
    print("验证结果汇总")
    print("=" * 80)
    print()

    print(f"总测试用例数: {total_tests}")
    print()

    if 'L1' in summary and 'total' in summary['L1']:
        print(f"L1 基本结构:     {summary['L1']['total']:3d} 项 ({summary['L1']['valid']} 有效)")
    if 'L1_EXP' in summary and 'total' in summary['L1_EXP']:
        print(f"L1 表达式级:     {summary['L1_EXP']['total']:3d} 项 ({summary['L1_EXP']['valid']} 有效)")
    if 'L1_CF' in summary and 'total' in summary['L1_CF']:
        print(f"L1 函数/类:      {summary['L1_CF']['total']:3d} 项 ({summary['L1_CF']['valid']} 有效)")
    if 'L2' in summary and 'total' in summary['L2']:
        print(f"L2 两层嵌套:     {summary['L2']['total']:3d} 项 ({summary['L2']['valid']} 有效)")
    if 'L2_EX' in summary and 'total' in summary['L2_EX']:
        print(f"L2 穷举组合:     {summary['L2_EX']['total']:3d} 项 ({summary['L2_EX']['valid']} 有效)")
    if 'L3' in summary and 'total' in summary['L3']:
        print(f"L3 三层嵌套:     {summary['L3']['total']:3d} 项 ({summary['L3']['valid']} 有效)")
    if 'L3_CO' in summary and 'total' in summary['L3_CO']:
        print(f"L3 三层组合:     {summary['L3_CO']['total']:3d} 项 ({summary['L3_CO']['valid']} 有效)")

    print()
    print("-" * 80)

    if total_tests >= 141:
        print("✓ 测试用例总数达标 (>=141)")
    else:
        print(f"✗ 测试用例总数未达标 (<141)，当前: {total_tests}")

    if all_valid:
        print("✓ 所有测试类的源代码都有效")
        print()
        print("★ 测试框架验证通过！可以开始运行测试。")
        print()
        print("运行命令：")
        print("  python run_tests.py                    # 运行所有测试")
        print("  python run_tests.py --level L1         # 只运行L1测试")
        print("  python run_tests.py --verbose          # 显示详细输出")
        print("  python -m pytest control_flow_matrix/  # 使用pytest运行")
    else:
        print("✗ 部分测试类存在问题，需要修复")
        print()
        print("请检查上述错误信息并修复相关测试类。")

    print("=" * 80)

    return 0 if (all_valid and total_tests >= 141) else 1


if __name__ == '__main__':
    sys.exit(main())
