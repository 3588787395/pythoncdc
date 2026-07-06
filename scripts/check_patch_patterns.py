#!/usr/bin/env python3
"""检查补丁模式的脚本"""

import sys
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def check_file(filename):
    """检查单个文件"""
    filepath = PROJECT_ROOT / filename
    if not filepath.exists():
        return {"file": filename, "errors": ["File not found"], "warnings": []}
    
    content = filepath.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    errors = []
    warnings = []
    
    # 检查危险模式
    danger_keywords = [
        (r'#\s*关键修复', "Contains '关键修复' comment", "error"),
        (r'#\s*[Kk]ey\s*[Ff]ix', "Contains 'Key Fix' comment", "error"),
        (r'def\s+_fix_\w+\s*\(', "Defines _fix_* function", "error"),
        (r'def\s+_patch_\w+\s*\(', "Defines _patch_* function", "error"),
        (r'def\s+_correct_\w+\s*\(', "Defines _correct_* function", "error"),
        (r'def\s+_generate_.*_from_block', "Contains _generate_*_from_block function", "error"),
        (r'def\s+_generate_nop_', "Contains _generate_nop_* function", "warning"),
    ]
    
    for pattern, msg, level in danger_keywords:
        matches = list(re.finditer(pattern, content))
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            line_text = lines[line_num-1].strip() if line_num > 0 else ""
            entry = f"{level}: {msg} at line {line_num}: {line_text}"
            if level == "error":
                errors.append(entry)
            else:
                warnings.append(entry)
    
    return {"file": filename, "errors": errors, "warnings": warnings}

def main():
    """主函数"""
    files_to_check = [
        "core/cfg/region_analyzer.py",
        "core/cfg/region_ast_generator.py",
    ]
    
    all_errors = []
    all_warnings = []
    
    print("="*80)
    print("PATCH PATTERN CHECK")
    print("="*80)
    
    for filename in files_to_check:
        print(f"\nChecking {filename}...")
        result = check_file(filename)
        
        if result["errors"]:
            print(f"  ERRORS in {filename}:")
            for err in result["errors"]:
                print(f"    {err}")
            all_errors.extend(result["errors"])
        
        if result["warnings"]:
            print(f"  WARNINGS in {filename}:")
            for warn in result["warnings"]:
                print(f"    {warn}")
            all_warnings.extend(result["warnings"])
        
        if not result["errors"] and not result["warnings"]:
            print(f"  ✓ OK")
    
    print("\n" + "="*80)
    if all_errors:
        print(f"❌ FAIL: Found {len(all_errors)} errors")
        return 1
    elif all_warnings:
        print(f"⚠️ PASS with {len(all_warnings)} warnings")
        return 0
    else:
        print("✅ PASS: No dangerous patterns found")
        return 0

if __name__ == "__main__":
    sys.exit(main())

