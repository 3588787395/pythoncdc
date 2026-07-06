#!/usr/bin/env python3
"""
Nook测试诊断脚本 - 识别所有导入和路径问题
"""
import os
import sys
import ast
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

NOOK_DIR = Path(__file__).parent / "nook"
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 已知问题模式
HARDCODED_PATHS = [
    r'd:\Desktop\ptrade相关\pythoncdc',
    r'D:\Desktop\ptrade相关\pythoncdc',
    '/home/user/pythoncdc',
]

MISSING_MODULES = {
    'tests.other.test_utils': 'tests/other/test_utils.py不存在',
    'parsers.ast_builder_cfg': 'parsers/ast_builder_cfg.py不存在',
}

def check_file(filepath):
    """检查单个测试文件的问题"""
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [{'type': 'READ_ERROR', 'line': 0, 'msg': str(e)}]
    
    # 检查硬编码路径
    for i, line in enumerate(lines, 1):
        for pattern in HARDCODED_PATHS:
            if pattern in line:
                issues.append({
                    'type': 'HARDCODED_PATH',
                    'line': i,
                    'msg': f'发现硬编码路径: {pattern}'
                })
    
    # 检查导入不存在的模块
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for mod_pattern, reason in MISSING_MODULES.items():
                    if mod_pattern in module:
                        issues.append({
                            'type': 'MISSING_MODULE',
                            'line': node.lineno,
                            'msg': f'导入不存在的模块: {module} ({reason})'
                        })
    except SyntaxError as e:
        issues.append({
            'type': 'SYNTAX_ERROR',
            'line': e.lineno or 0,
            'msg': f'语法错误: {e.msg}'
        })
    
    return issues

def main():
    """主函数"""
    print("=" * 80)
    print("NOOK测试诊断报告")
    print("=" * 80)
    
    py_files = list(NOOK_DIR.glob("*.py"))
    total_files = len(py_files)
    
    print(f"\n总测试文件数: {total_files}")
    print("-" * 80)
    
    issue_stats = {
        'HARDCODED_PATH': 0,
        'MISSING_MODULE': 0,
        'SYNTAX_ERROR': 0,
        'READ_ERROR': 0,
    }
    
    files_with_issues = []
    clean_files = []
    
    for filepath in sorted(py_files):
        issues = check_file(filepath)
        
        if issues:
            files_with_issues.append((filepath.name, issues))
            for issue in issues:
                issue_stats[issue['type']] = issue_stats.get(issue['type'], 0) + 1
        else:
            clean_files.append(filepath.name)
    
    # 输出统计
    print(f"\n✓ 无问题文件: {len(clean_files)}")
    print(f"✗ 有问题文件: {len(files_with_issues)}")
    print(f"\n问题类型统计:")
    for issue_type, count in sorted(issue_stats.items()):
        print(f"  - {issue_type}: {count}处")
    
    # 详细输出有问题文件
    if files_with_issues:
        print(f"\n{'=' * 80}")
        print("详细问题列表:")
        print('=' * 80)
        
        for filename, issues in files_with_issues:
            print(f"\n📄 {filename}")
            for issue in issues:
                print(f"  [L{issue['line']:3d}] {issue['type']}: {issue['msg']}")
    
    # 输出健康文件列表（前20个）
    if clean_files:
        print(f"\n{'=' * 80}")
        print(f"健康文件示例 (共{len(clean_files)}个):")
        print('=' * 80)
        for name in clean_files[:20]:
            print(f"  ✓ {name}")
        if len(clean_files) > 20:
            print(f"  ... 还有 {len(clean_files) - 20} 个")
    
    # 计算可运行率
    runnable_rate = len(clean_files) / total_files * 100 if total_files > 0 else 0
    print(f"\n{'=' * 80}")
    print(f"预估可运行率: {runnable_rate:.1f}%")
    print('=' * 80)
    
    return {
        'total': total_files,
        'clean': len(clean_files),
        'issues': len(files_with_issues),
        'stats': issue_stats,
        'runnable_rate': runnable_rate
    }

if __name__ == '__main__':
    result = main()
