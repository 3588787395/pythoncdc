#!/usr/bin/env python3
import sys
import os
import types
import importlib.util

# Add paths
sys.path.insert(0, '.')
sys.path.insert(0, 'testqouter/round1')

# Import comparison functions
from testqouter.round1.base import compare_bytecode, get_bytecode_instructions

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
ok_py = "site-packages/IQCommon/api/klinedataOK.py"

print(f"比较: {target_pyc} <-> {ok_py}\n")

# Load original pyc
import pyc_loader_v2
original_code = pyc_loader_v2.load_pyc(target_pyc)

# Compile OK.py
spec = importlib.util.spec_from_file_location("ok_module", ok_py)
ok_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ok_module)
decompiled_code = ok_module.__compiled__ if hasattr(ok_module, '__compiled__') else None

if decompiled_code is None:
    # Try getting from __dict__ 
    decompiled_code = ok_module

# Compare
result = compare_bytecode(original_code, decompiled_code)

print(f"匹配率: {result['match_rate']:.2%}")
print(f"匹配函数: {result['matched']}/{result['total']}")
print(f"\n不匹配函数 (前20个):")

mismatched = []
for func_name, details in result['functions'].items():
    if details['true_diffs'] > 0:
        mismatched.append((func_name, details['true_diffs'], details.get('first_diff', '')))

for func, diffs, first_diff in sorted(mismatched, key=lambda x: -x[1])[:20]:
    print(f"  {diffs} diffs - {func}: {first_diff[:80] if first_diff else 'N/A'}")

# Save to report
report_dir = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_61/test_engineer"
os.makedirs(report_dir, exist_ok=True)

with open(f"{report_dir}/decompile_report.md", 'w', encoding='utf-8') as f:
    f.write(f"""# 测试工程师报告 - Round 61

## 目标文件
- **pyc路径**: `{target_pyc}`
- **反编译输出**: `{ok_py}`

## 字节码一致性结果
- **匹配率**: {result['match_rate']:.2%}
- **匹配函数数**: {result['matched']} / {result['total']}
- **不匹配函数数**: {len(mismatched)}

## 不匹配函数清单

| 函数名 | 差异数 | 首个差异 |
|--------|--------|----------|
""")
    for func, diffs, first_diff in sorted(mismatched, key=lambda x: -x[1]):
        f.write(f"| {func} | {diffs} | {first_diff[:100] if first_diff else 'N/A'} |\n")

    f.write(f"""

## 分析结论

**当前状态**: {'100% 一致' if result['match_rate'] == 1.0 else f'部分一致 ({result["matched"]}/{result["total"]})'}

**主要问题**:
- 共 {len(mismatched)} 个函数存在字节码差异
- 最高差异: {max([d for _, d, _ in mismatched]) if mismatched else 0} 条指令

**下一步行动**:
{f"- 本文件已达 100% 一致，豁免最小复现实例要求" if result['match_rate'] == 1.0 else f"- 创建 10+ 个最小复现实例"}

## 与上一轮对比
- 上一轮 (R60): 全局匹配率 89.07%
- 本轮 (R61): 本文件匹配率 {result['match_rate']:.2%}
""")

print(f"\n报告已保存至: {report_dir}/decompile_report.md")