#!/usr/bin/env python3
"""第1轮测试工程师脚本：验证decompiler_test_comprehensive.cpython-311.pyc"""

import sys
import os
import json
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from compare_bytecode_simple import compare_pyc_files
from compare_bytecode_v2 import compare_pyc_files as compare_pyc_files_v2

def main():
    orig_pyc = "decompiler_test_comprehensive.cpython-311.pyc"
    decomp_py = "decompiler_test_comprehensive_decompiled_round01.py"
    
    print("=== 第1轮测试工程师报告 ===")
    print(f"目标文件: {orig_pyc}")
    print(f"反编译文件: {decomp_py}")
    
    # 检查文件存在
    if not os.path.exists(orig_pyc):
        print(f"错误: 原始pyc文件 {orig_pyc} 不存在")
        return
    
    if not os.path.exists(decomp_py):
        print(f"错误: 反编译py文件 {decomp_py} 不存在")
        return
    
    # 执行字节码比较
    try:
        print("\n1. 执行字节码比较...")
        result = compare_pyc_files_v2(orig_pyc, decomp_py)
        
        # 输出结果
        print(f"总函数数: {result['total_functions']}")
        print(f"匹配函数数: {result['matched']}")
        print(f"成功率: {result['success_rate']:.2f}%")
        print(f"不匹配函数数: {len(result['mismatches'])}")
        
        # 保存详细报告
        report_data = {
            'round': 1,
            'timestamp': '2026-08-19',
            'baseline_success_rate': 87.50,
            'current_success_rate': result['success_rate'],
            'total_functions': result['total_functions'],
            'matched_functions': result['matched'],
            'mismatched_count': len(result['mismatches']),
            'mismatches': result['mismatches'],
            'syntax_error': result.get('syntax_error')
        }
        
        # 保存报告到指定位置
        report_dir = Path(".trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_01/test_engineer")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_dir / "decompile_report.md", 'w', encoding='utf-8') as f:
            f.write("# 第1轮测试工程师报告\n\n")
            f.write(f"## 测试结果摘要\n")
            f.write(f"- 测试时间: 2026-08-19\n")
            f.write(f"- 总函数数: {result['total_functions']}\n")
            f.write(f"- 匹配函数数: {result['matched']}\n")
            f.write(f"- 成功率: {result['success_rate']:.2f}%\n")
            f.write(f"- 基准成功率: 87.50%\n")
            
            if result.get('syntax_error'):
                f.write(f"\n## 语法错误\n")
                f.write(f"反编译文件存在语法错误: {result['syntax_error']}\n")
            
            if result['mismatches']:
                f.write(f"\n## 不匹配函数详情\n")
                for i, m in enumerate(result['mismatches'], 1):
                    f.write(f"\n### 不匹配函数 {i}: {m['function']}\n")
                    if 'error' in m:
                        f.write(f"- 错误: {m['error']}\n")
                    else:
                        f.write(f"- 差异总数: {m['total_diffs']}\n")
                        f.write(f"- 原始指令数: {m.get('orig_count', '?')}\n")
                        f.write(f"- 反编译指令数: {m.get('decomp_count', '?')}\n")
                        
                        # 显示前5个差异
                        f.write(f"\n前5个差异:\n")
                        for j, diff in enumerate(m.get('diffs', [])[:5], 1):
                            orig = diff.get('original', 'N/A')
                            decomp = diff.get('decompiled', 'N/A')
                            f.write(f"  {j}. 偏移 {diff['offset']}: 原始='{orig}' 反编译='{decomp}'\n")
        
        # 保存JSON数据
        with open(report_dir / "decompile_data.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n报告已保存到: {report_dir}")
        print(f"需要修复的函数数: {len(result['mismatches'])}")
        
    except Exception as e:
        print(f"执行字节码比较时出错: {e}")
        traceback.print_exc()
        
        # 记录错误
        report_dir = Path(".trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_01/test_engineer")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        with open(report_dir / "decompile_report.md", 'w', encoding='utf-8') as f:
            f.write("# 第1轮测试工程师报告\n\n")
            f.write(f"## 错误\n")
            f.write(f"字节码比较执行失败: {e}\n")
            f.write(f"\n```\n")
            f.write(traceback.format_exc())
            f.write(f"\n```\n")

if __name__ == '__main__':
    main()