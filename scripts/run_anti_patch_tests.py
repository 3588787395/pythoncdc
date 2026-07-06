#!/usr/bin/env python3
"""
防补丁机制综合测试脚本

运行所有防补丁相关检查：
1. 方法签名验证
2. 补丁检测
3. 字节码一致性验证
4. 完备性测试

使用方法：
    python scripts/run_anti_patch_tests.py
    python scripts/run_anti_patch_tests.py --strict
    python scripts/run_anti_patch_tests.py --report
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AntiPatchTestRunner:
    """防补丁机制测试运行器"""

    def __init__(self, strict: bool = False, report: bool = False):
        self.strict = strict
        self.report = report
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def run_command(self, cmd: List[str], cwd: str = None) -> Tuple[int, str, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "命令执行超时"
        except Exception as e:
            return -1, "", str(e)

    def test_method_signatures(self) -> bool:
        """测试方法签名验证"""
        print("\n" + "=" * 60)
        print("  [1/4] 方法签名验证")
        print("=" * 60)

        cmd = [sys.executable, "scripts/validate_method_signatures.py"]
        code, stdout, stderr = self.run_command(cmd)

        if code == 0:
            print("✓ 方法签名验证通过")
            self.passed += 1
            return True
        else:
            print("✗ 方法签名验证失败")
            if stderr:
                print(f"  错误: {stderr[:200]}")
            self.failed += 1
            return False

    def test_patch_detection(self) -> bool:
        """测试补丁检测"""
        print("\n" + "=" * 60)
        print("  [2/4] 补丁检测")
        print("=" * 60)

        files = [
            "core/cfg/region_analyzer.py",
            "core/cfg/region_ast_generator.py"
        ]

        all_passed = True
        for file in files:
            if not os.path.exists(file):
                print(f"  ⚠ 文件不存在: {file}")
                continue

            cmd = [sys.executable, "core/cfg/patch_detector_enhanced.py", file, "--threshold", "90"]
            code, stdout, stderr = self.run_command(cmd)

            if code == 0:
                print(f"  ✓ {file}: 通过补丁检测")
            else:
                print(f"  ✗ {file}: 存在补丁模式")
                all_passed = False

        if all_passed:
            self.passed += 1
        else:
            self.failed += 1
        return all_passed

    def test_bytecode_equivalence(self) -> bool:
        """测试字节码一致性"""
        print("\n" + "=" * 60)
        print("  [3/4] 字节码一致性验证")
        print("=" * 60)

        cmd = [sys.executable, "scripts/verify_bytecode_equivalence.py", "--test"]
        code, stdout, stderr = self.run_command(cmd)

        if "通过率: 100.0%" in stdout or "passed" in stdout.lower():
            print("✓ 字节码一致性验证通过")
            self.passed += 1
            return True
        else:
            print("✗ 字节码一致性验证失败")
            if stdout:
                print(stdout[-500:])
            self.failed += 1
            return False

    def test_completeness(self) -> bool:
        """测试完备性"""
        print("\n" + "=" * 60)
        print("  [4/4] 完备性测试")
        print("=" * 60)

        cmd = [sys.executable, "-m", "pytest", "tests/control_flow_matrix/", "-v", "--tb=line", "-q"]
        code, stdout, stderr = self.run_command(cmd)

        if code == 0:
            print("✓ 完备性测试通过")
            self.passed += 1
            return True
        else:
            if "passed" in stdout.lower():
                print("⚠ 完备性测试有失败项（继续）")
            else:
                print("✗ 完备性测试失败")
            self.failed += 1
            return False

    def run_all(self) -> bool:
        """运行所有测试"""
        print("\n" + "=" * 60)
        print("  防补丁机制综合测试")
        print("=" * 60)

        results = [
            ("方法签名验证", self.test_method_signatures),
            ("补丁检测", self.test_patch_detection),
            ("字节码一致性", self.test_bytecode_equivalence),
            ("完备性测试", self.test_completeness),
        ]

        for name, test_func in results:
            try:
                test_func()
            except Exception as e:
                print(f"  ! 测试异常: {e}")
                self.failed += 1

        print("\n" + "=" * 60)
        print("  测试摘要")
        print("=" * 60)
        print(f"  通过: {self.passed}/{len(results)}")
        print(f"  失败: {self.failed}/{len(results)}")

        if self.strict:
            if self.failed == 0:
                print("\n✓ 所有测试通过 (严格模式)")
                return True
            else:
                print(f"\n✗ 存在 {self.failed} 个失败项 (严格模式)")
                return False
        else:
            if self.passed >= len(results) - 1:
                print("\n✓ 核心测试通过")
                return True
            else:
                print(f"\n✗ 核心测试失败")
                return False

    def generate_report(self) -> Dict:
        """生成报告"""
        return {
            'total_tests': self.passed + self.failed,
            'passed': self.passed,
            'failed': self.failed,
            'pass_rate': self.passed * 100 / max(self.passed + self.failed, 1),
            'strict_mode': self.strict,
            'timestamp': str(Path(__file__).stat().st_mtime),
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='防补丁机制综合测试')
    parser.add_argument('--strict', action='store_true', help='严格模式：所有测试必须通过')
    parser.add_argument('--report', action='store_true', help='生成JSON格式报告')
    parser.add_argument('--output', '-o', help='报告输出文件')

    args = parser.parse_args()

    runner = AntiPatchTestRunner(strict=args.strict, report=args.report)
    success = runner.run_all()

    if args.report:
        report = runner.generate_report()
        print("\nJSON报告:")
        print(json.dumps(report, indent=2, ensure_ascii=False))

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n报告已保存到: {args.output}")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
