#!/usr/bin/env python3
"""
自动化测试执行器

用于执行测试用例并生成测试报告
"""

import sys
import time
import json
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from patterns.tests.test_case_manager import TestCaseManager, TestCase, TestResult, TestStatus

@dataclass
class TestReport:
    """测试报告数据类"""
    test_run_id: str
    timestamp: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: float
    results: List[Dict]
    summary: Dict
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

class TestRunner:
    """测试执行器"""
    
    def __init__(self, pycdc_path: str = "pycdc.py"):
        self.pycdc_path = pycdc_path
        self.test_case_manager = TestCaseManager()
        self.results: List[TestResult] = []
    
    def compile_source(self, source_code: str) -> Optional[bytes]:
        """编译源代码为字节码"""
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                # 创建临时文件
                temp_py = tmpdir_path / 'test.py'
                temp_py.write_text(source_code, encoding='utf-8')
                
                # 编译为字节码
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(temp_py)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"编译失败: {result.stderr}")
                    return None
                
                # 查找生成的 .pyc 文件 (可能在 __pycache__ 目录中)
                pycache_dir = tmpdir_path / '__pycache__'
                if pycache_dir.exists():
                    pyc_files = list(pycache_dir.glob('*.pyc'))
                    if pyc_files:
                        with open(pyc_files[0], 'rb') as f:
                            return f.read()
                
                # 直接查找 .pyc 文件
                temp_pyc = tmpdir_path / 'test.pyc'
                if temp_pyc.exists():
                    with open(temp_pyc, 'rb') as f:
                        return f.read()
                
                print("编译失败: 未找到生成的 .pyc 文件")
                return None
            
        except Exception as e:
            print(f"编译失败: {e}")
            return None
    
    def run_decompiler(self, bytecode: bytes) -> Optional[str]:
        """运行反编译器"""
        try:
            # 创建临时字节码文件
            with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False) as f:
                # 写入 Python 3.11 的 pyc 文件头
                f.write(b'\x55\x0d\x0d\x0a')  # Magic number
                f.write(b'\x00\x00\x00\x00')  # Timestamp
                f.write(b'\x00\x00\x00\x00')  # Size
                f.write(b'\x00\x00\x00\x00')  # Hash (Python 3.11+)
                f.write(bytecode)
                temp_pyc = f.name
            
            # 运行反编译器
            result = subprocess.run(
                [sys.executable, self.pycdc_path, temp_pyc],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 清理临时文件
            Path(temp_pyc).unlink(missing_ok=True)
            
            return result.stdout
            
        except subprocess.TimeoutExpired:
            print("反编译超时")
            return None
        except Exception as e:
            print(f"反编译失败: {e}")
            return None
    
    def run_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        start_time = time.time()
        test_id = test_case.get_id()
        
        try:
            # 编译源代码
            bytecode = self.compile_source(test_case.source_code)
            if bytecode is None:
                return TestResult(
                    test_id=test_id,
                    test_name=test_case.name,
                    pattern_type=test_case.pattern_type,
                    status=TestStatus.FAILED,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message="编译失败"
                )
            
            # 运行反编译器
            output = self.run_decompiler(bytecode)
            if output is None:
                return TestResult(
                    test_id=test_id,
                    test_name=test_case.name,
                    pattern_type=test_case.pattern_type,
                    status=TestStatus.FAILED,
                    duration_ms=(time.time() - start_time) * 1000,
                    error_message="反编译失败"
                )
            
            # 检查反编译结果
            if test_case.expected_output:
                if test_case.expected_output.strip() == output.strip():
                    status = TestStatus.PASSED
                    diff = None
                else:
                    status = TestStatus.FAILED
                    diff = self.generate_diff(test_case.expected_output, output)
            else:
                # 没有期望输出，只检查是否成功反编译
                status = TestStatus.PASSED if output.strip() else TestStatus.FAILED
                diff = None
            
            return TestResult(
                test_id=test_id,
                test_name=test_case.name,
                pattern_type=test_case.pattern_type,
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                actual_output=output,
                diff=diff
            )
            
        except Exception as e:
            return TestResult(
                test_id=test_id,
                test_name=test_case.name,
                pattern_type=test_case.pattern_type,
                status=TestStatus.FAILED,
                duration_ms=(time.time() - start_time) * 1000,
                error_message=str(e)
            )
    
    def generate_diff(self, expected: str, actual: str) -> str:
        """生成差异信息"""
        import difflib
        diff = difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile='expected',
            tofile='actual'
        )
        return ''.join(diff)
    
    def run_all_tests(self, pattern_type: Optional[str] = None, 
                     tag: Optional[str] = None) -> TestReport:
        """运行所有测试"""
        # 获取测试用例
        if pattern_type:
            test_cases = self.test_case_manager.get_test_cases_by_pattern(pattern_type)
        elif tag:
            test_cases = self.test_case_manager.get_test_cases_by_tag(tag)
        else:
            test_cases = self.test_case_manager.get_all_test_cases()
        
        print(f"\n开始运行 {len(test_cases)} 个测试用例...")
        print("=" * 60)
        
        # 运行测试
        self.results = []
        start_time = time.time()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] {test_case.name}...", end=" ")
            result = self.run_test(test_case)
            self.results.append(result)
            
            if result.status == TestStatus.PASSED:
                print(f"[OK] ({result.duration_ms:.1f}ms)")
            else:
                print(f"[FAIL] ({result.duration_ms:.1f}ms)")
                if result.error_message:
                    print(f"  错误: {result.error_message}")
        
        total_duration = (time.time() - start_time) * 1000
        
        # 生成报告
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        
        report = TestReport(
            test_run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            timestamp=datetime.now().isoformat(),
            total=len(test_cases),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_ms=total_duration,
            results=[r.to_dict() for r in self.results],
            summary={
                'pass_rate': passed / len(test_cases) * 100 if test_cases else 0,
                'avg_duration_ms': total_duration / len(test_cases) if test_cases else 0
            }
        )
        
        return report
    
    def save_report(self, report: TestReport, output_file: str = "test_report.json"):
        """保存测试报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report.to_json())
        print(f"\n测试报告已保存到: {output_file}")
    
    def print_summary(self, report: TestReport):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        print(f"测试运行ID: {report.test_run_id}")
        print(f"总测试数: {report.total}")
        print(f"通过: {report.passed}")
        print(f"失败: {report.failed}")
        print(f"跳过: {report.skipped}")
        print(f"通过率: {report.summary['pass_rate']:.1f}%")
        print(f"总耗时: {report.duration_ms:.1f}ms")
        print(f"平均耗时: {report.summary['avg_duration_ms']:.1f}ms")
        print("=" * 60)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="运行模式测试")
    parser.add_argument("--pattern", help="指定模式类型")
    parser.add_argument("--tag", help="指定标签")
    parser.add_argument("--output", default="test_report.json", help="输出文件")
    parser.add_argument("--pycdc", default="pycdc.py", help="pycdc 路径")
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = TestRunner(pycdc_path=args.pycdc)
    
    # 运行测试
    report = runner.run_all_tests(pattern_type=args.pattern, tag=args.tag)
    
    # 打印摘要
    runner.print_summary(report)
    
    # 保存报告
    runner.save_report(report, args.output)
    
    # 返回退出码
    return 0 if report.failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
