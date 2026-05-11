import subprocess
import sys
from pathlib import Path
from collections import defaultdict


def discover_tests(test_dir: Path) -> dict:
    """发现并按层级分组的测试文件"""
    levels = {
        'L1_basic': test_dir / 'L1_basic',
        'L2_nested_two': test_dir / 'L2_nested_two',
        'L3_nested_three': test_dir / 'L3_nested_three',
    }

    tests_by_level = {}
    for level_name, level_dir in levels.items():
        if level_dir.exists():
            test_files = list(level_dir.glob('test_*.py'))
            tests_by_level[level_name] = test_files

    return tests_by_level


def run_pytest_tests() -> subprocess.CompletedProcess:
    """使用 pytest 运行所有控制流完备性测试"""
    test_dir = Path(__file__).parent

    cmd = [
        sys.executable, '-m', 'pytest',
        str(test_dir),
        '-v', '--tb=short', '--no-header'
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=test_dir.parent.parent
    )

    return result


def parse_test_results(output: str) -> dict:
    """解析 pytest 输出，提取测试结果"""
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'by_level': defaultdict(lambda: {'total': 0, 'passed': 0, 'failed': 0}),
        'failed_cases': []
    }

    lines = output.split('\n')
    for line in lines:
        line = line.strip()

        if 'PASSED' in line:
            results['total'] += 1
            results['passed'] += 1
            level = _detect_level(line)
            results['by_level'][level]['total'] += 1
            results['by_level'][level]['passed'] += 1

        elif 'FAILED' in line:
            results['total'] += 1
            results['failed'] += 1
            level = _detect_level(line)
            results['by_level'][level]['total'] += 1
            results['by_level'][level]['failed'] += 1

            case_info = _extract_case_name(line)
            if case_info:
                results['failed_cases'].append(case_info)

        elif 'ERROR' in line:
            results['errors'] += 1

    return results


def _detect_level(line: str) -> str:
    """从测试行中检测所属层级"""
    if 'L1_basic' in line or '/L1_' in line:
        return 'L1_basic'
    elif 'L2_nested_two' in line or '/L2_' in line:
        return 'L2_nested_two'
    elif 'L3_nested_three' in line or '/L3_' in line:
        return 'L3_nested_three'
    return 'unknown'


def _extract_case_name(line: str) -> dict:
    """提取失败用例的名称信息"""
    parts = line.split('::')
    if len(parts) >= 2:
        file_path = parts[0]
        test_name = parts[1].split()[0] if len(parts[1].split()) > 0 else parts[1]
        return {
            'file': file_path,
            'name': test_name,
            'full_id': line.split()[0] if line.split() else line
        }
    return None


def generate_report(results: dict) -> str:
    """生成格式化的文本报告"""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("控制流完备性测试报告")
    report_lines.append("Control Flow Completeness Test Report")
    report_lines.append("=" * 80)
    report_lines.append("")

    total = results['total']
    passed = results['passed']
    failed = results['failed']
    errors = results['errors']
    pass_rate = (passed / total * 100) if total > 0 else 0

    report_lines.append(f"{'总体统计':=^40}")
    report_lines.append(f"  总测试数: {total}")
    report_lines.append(f"  通过数量: {passed}")
    report_lines.append(f"  失败数量: {failed}")
    report_lines.append(f"  错误数量: {errors}")
    report_lines.append(f"  通过率:   {pass_rate:.1f}%")
    report_lines.append("")

    report_lines.append(f"{'各层级详情':=^40}")

    level_order = ['L1_basic', 'L2_nested_two', 'L3_nested_three']
    level_names = {
        'L1_basic': 'L1 基础控制流',
        'L2_nested_two': 'L2 二层嵌套',
        'L3_nested_three': 'L3 三层嵌套'
    }

    for level_key in level_order:
        if level_key in results['by_level']:
            level_data = results['by_level'][level_key]
            l_total = level_data['total']
            l_passed = level_data['passed']
            l_failed = level_data['failed']
            l_rate = (l_passed / l_total * 100) if l_total > 0 else 0

            display_name = level_names.get(level_key, level_key)
            status_icon = "✓" if l_failed == 0 else "✗"

            report_lines.append(f"\n  [{status_icon}] {display_name} ({level_key})")
            report_lines.append(f"      总计: {l_total} | 通过: {l_passed} | 失败: {l_failed} | 通过率: {l_rate:.1f}%")

    report_lines.append("")
    report_lines.append("-" * 80)

    if results['failed_cases']:
        report_lines.append(f"\n失败用例列表 ({len(results['failed_cases'])} 个):")
        report_lines.append("-" * 80)

        for idx, case in enumerate(results['failed_cases'], 1):
            report_lines.append(f"\n  {idx}. {case.get('name', case.get('full_id', 'Unknown'))}")
            report_lines.append(f"     文件: {case.get('file', 'N/A')}")
    else:
        report_lines.append("\n✓ 所有测试均通过！")

    report_lines.append("")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


def main():
    """主函数：运行测试套件并生成报告"""
    print("\n正在启动控制流完备性测试套件...")
    print("=" * 80)

    result = run_pytest_tests()

    print("\n原始测试输出:")
    print("-" * 80)
    print(result.stdout)
    if result.stderr:
        print("错误输出:")
        print(result.stderr)

    results = parse_test_results(result.stdout)

    report = generate_report(results)
    print("\n\n" + report)

    output_file = Path(__file__).parent / 'completeness_report.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
        f.write("\n\n原始输出:\n")
        f.write(result.stdout)

    print(f"\n完整报告已保存至: {output_file}")

    if results['failed'] > 0 or results['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
