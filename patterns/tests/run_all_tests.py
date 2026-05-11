#!/usr/bin/env python3
"""
测试入口脚本

用于运行所有模式测试
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from patterns.tests.test_case_manager import initialize_test_cases
from patterns.tests.test_runner import TestRunner

def main():
    """主函数"""
    print("=" * 70)
    print("模式识别系统测试套件")
    print("=" * 70)
    
    # 初始化测试用例
    print("\n[1/3] 初始化测试用例...")
    manager = initialize_test_cases()
    stats = manager.get_statistics()
    print(f"  已加载 {stats['total']} 个测试用例")
    print(f"  覆盖 {len(stats['by_pattern'])} 种模式")
    
    # 创建测试运行器
    print("\n[2/3] 准备测试环境...")
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    pycdc_path = os.path.join(project_root, "pycdc.py")
    runner = TestRunner(pycdc_path=pycdc_path)
    
    # 运行所有测试
    print("\n[3/3] 运行测试...")
    report = runner.run_all_tests()
    
    # 打印摘要
    runner.print_summary(report)
    
    # 保存报告
    runner.save_report(report, "test_report.json")
    
    # 返回退出码
    if report.failed == 0:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print(f"\n❌ {report.failed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
