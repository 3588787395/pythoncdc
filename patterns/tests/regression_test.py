#!/usr/bin/env python3
"""
回归测试系统

用于跟踪和管理回归测试，确保修复不会引入新问题
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from patterns.tests.test_case_manager import TestCaseManager, TestResult, TestStatus

@dataclass
class RegressionRecord:
    """回归测试记录"""
    record_id: str
    test_id: str
    test_name: str
    pattern_type: str
    issue_description: str
    fix_commit: str
    first_passed: str
    last_checked: str
    status: str  # 'stable', 'flaky', 'regressed'
    check_count: int
    pass_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)

class RegressionTestSystem:
    """回归测试系统"""
    
    def __init__(self, regression_file: str = "regression_records.json"):
        self.regression_file = regression_file
        self.records: Dict[str, RegressionRecord] = {}
        self.load_records()
    
    def load_records(self):
        """加载回归测试记录"""
        try:
            with open(self.regression_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    record = RegressionRecord(**item)
                    self.records[record.test_id] = record
        except FileNotFoundError:
            pass
    
    def save_records(self):
        """保存回归测试记录"""
        data = [r.to_dict() for r in self.records.values()]
        with open(self.regression_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_regression_test(self, test_id: str, test_name: str, 
                           pattern_type: str, issue_description: str,
                           fix_commit: str = ""):
        """添加回归测试"""
        record = RegressionRecord(
            record_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            test_id=test_id,
            test_name=test_name,
            pattern_type=pattern_type,
            issue_description=issue_description,
            fix_commit=fix_commit,
            first_passed=datetime.now().isoformat(),
            last_checked=datetime.now().isoformat(),
            status='stable',
            check_count=0,
            pass_count=0
        )
        self.records[test_id] = record
        self.save_records()
        return record.record_id
    
    def update_test_result(self, test_id: str, passed: bool):
        """更新测试结果"""
        if test_id not in self.records:
            return False
        
        record = self.records[test_id]
        record.check_count += 1
        record.last_checked = datetime.now().isoformat()
        
        if passed:
            record.pass_count += 1
            # 检查是否稳定
            if record.pass_count >= 5:  # 连续5次通过视为稳定
                record.status = 'stable'
        else:
            # 测试失败，可能是回归
            record.status = 'regressed'
        
        self.save_records()
        return True
    
    def get_regressed_tests(self) -> List[RegressionRecord]:
        """获取回归的测试"""
        return [r for r in self.records.values() if r.status == 'regressed']
    
    def get_stable_tests(self) -> List[RegressionRecord]:
        """获取稳定的测试"""
        return [r for r in self.records.values() if r.status == 'stable']
    
    def get_flaky_tests(self) -> List[RegressionRecord]:
        """获取不稳定的测试"""
        return [r for r in self.records.values() if r.status == 'flaky']
    
    def generate_report(self) -> Dict:
        """生成回归测试报告"""
        total = len(self.records)
        stable = len(self.get_stable_tests())
        regressed = len(self.get_regressed_tests())
        flaky = len(self.get_flaky_tests())
        
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': total,
                'stable': stable,
                'regressed': regressed,
                'flaky': flaky,
                'stability_rate': stable / total * 100 if total > 0 else 0
            },
            'regressed_tests': [
                {
                    'test_id': r.test_id,
                    'test_name': r.test_name,
                    'pattern_type': r.pattern_type,
                    'issue': r.issue_description
                }
                for r in self.get_regressed_tests()
            ]
        }

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="回归测试系统")
    parser.add_argument("--add", help="添加回归测试", action="store_true")
    parser.add_argument("--test-id", help="测试ID")
    parser.add_argument("--test-name", help="测试名称")
    parser.add_argument("--pattern", help="模式类型")
    parser.add_argument("--issue", help="问题描述")
    parser.add_argument("--report", help="生成报告", action="store_true")
    
    args = parser.parse_args()
    
    system = RegressionTestSystem()
    
    if args.add:
        if not all([args.test_id, args.test_name, args.pattern, args.issue]):
            print("错误: 添加回归测试需要提供 --test-id, --test-name, --pattern, --issue")
            return 1
        
        record_id = system.add_regression_test(
            args.test_id, args.test_name, args.pattern, args.issue
        )
        print(f"已添加回归测试: {record_id}")
    
    elif args.report:
        report = system.generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    else:
        print("回归测试系统")
        print(f"总记录数: {len(system.records)}")
        print(f"稳定: {len(system.get_stable_tests())}")
        print(f"回归: {len(system.get_regressed_tests())}")
        print(f"不稳定: {len(system.get_flaky_tests())}")

if __name__ == "__main__":
    sys.exit(main())
