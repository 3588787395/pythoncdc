#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

import subprocess
import os
from pathlib import Path

# 目标 pyc 文件
target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
ok_py = "site-packages/IQCommon/api/klinedataOK.py"

print(f"=== 测试工程师 - Round 61 ===")
print(f"目标文件: {target_pyc}")
print(f"预期输出: {ok_py}\n")

# 1. 反编译
print("1. 反编译中...")
result = subprocess.run(
    ["python", "pycdc.py", target_pyc, "-o", ok_py],
    capture_output=True,
    text=True,
    timeout=60
)
print(f"反编译完成，返回码: {result.returncode}")
if result.stdout:
    print(f"stdout: {result.stdout[:500]}")
if result.stderr:
    print(f"stderr: {result.stderr[:500]}")

# 2. 字节码比较
print("\n2. 字节码比较中...")
result = subprocess.run(
    ["python", "testqouter/round1/base.py", target_pyc, ok_py],
    capture_output=True,
    text=True,
    timeout=60
)
print(f"字节码比较完成，返回码: {result.returncode}")

# 解析结果
match_rate = 0.0
matched = 0
total = 0
mismatched_funcs = []

for line in result.stdout.split('\n'):
    if "Bytecode Match Rate:" in line:
        match_rate = float(line.split(":")[1].strip().rstrip("%")) / 100
    if "Matched Functions:" in line:
        parts = line.split(":")[1].strip().split("/")
        matched = int(parts[0])
        total = int(parts[1])
    if "true_diffs" in line and " -> " in line:
        parts = line.split()
        if len(parts) >= 2:
            func_name = parts[1]
            try:
                diffs = int(parts[0])
                if diffs > 0:
                    mismatched_funcs.append((func_name, diffs))
            except:
                pass

print(f"\n结果:")
print(f"  匹配率: {match_rate:.2%}")
print(f"  匹配函数: {matched}/{total}")
print(f"\n不匹配函数 (前15个):")
for func, diffs in sorted(mismatched_funcs, key=lambda x: -x[1])[:15]:
    print(f"  {diffs} diffs - {func}")

# 保存结果到文件
output_dir = Path(".trae/specs/region-comment-multi-pyc-iteration/rounds/round_61/test_engineer")
output_dir.mkdir(parents=True, exist_ok=True)

report_path = output_dir / "decompile_report.md"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(f"""# 测试工程师报告 - Round 61

## 目标文件
- **pyc路径**: `{target_pyc}`
- **反编译输出**: `{ok_py}`

## 字节码一致性结果
- **匹配率**: {match_rate:.2%}
- **匹配函数数**: {matched} / {total}
- **不匹配函数数**: {len(mismatched_funcs)}

## 不匹配函数清单

| 函数名 | 差异数 | 差异类型 |
|--------|--------|----------|
""")
    for func, diffs in sorted(mismatched_funcs, key=lambda x: -x[1]):
        f.write(f"| {func} | {diffs} | 待分析 |\n")

    f.write(f"""

## 分析结论

**当前状态**: {'100% 一致' if match_rate == 1.0 else '部分一致'}

**主要问题**:
- 共 {len(mismatched_funcs)} 个函数存在字节码差异
- 最高差异函数差异达 {max(mismatched_funcs, key=lambda x: x[1])[1] if mismatched_funcs else 0} 条指令

**下一步行动**:
- 创建 {min(12, len(mismatched_funcs)) + (10 if len(mismatched_funcs) < 10 else 0)} 个最小复现实例
- 分析差异模式，定位到具体的区域识别或AST生成问题

## 与上一轮对比
- 上一轮 (R60): 全局匹配率 89.07%
- 本轮 (R61): 本文件匹配率 {match_rate:.2%}
- 变化: 需要修复工程师确认
""")

print(f"\n报告已保存至: {report_path}")