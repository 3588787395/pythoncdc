#!/usr/bin/env python3
"""验证所有复现实例 - Round 61"""

import subprocess
import sys
import os
from pathlib import Path

repro_dir = Path(".trae/specs/region-comment-multi-pyc-iteration/rounds/round_61/test_engineer/minimal_repros")
results = []

print("验证复现实例...\n")

for i in range(1, 13):
    filename = f"repro_{i:02d}_*.py"
    repro_files = list(repro_dir.glob(filename))
    
    if not repro_files:
        continue
        
    repro_file = repro_files[0]
    
    # 1. 编译源文件
    pyc_path = repro_file.with_suffix('.pyc')
    subprocess.run(
        ["python", "-m", "py_compile", str(repro_file)],
        capture_output=True,
        timeout=5
    )
    
    if not pyc_path.exists():
        # 尝试查找 __pycache__ 中的 pyc
        cache_dir = repro_file.parent.parent.parent.parent / "__pycache__"
        cache_pyc = list(cache_dir.glob(f"{repro_file.stem}.*.pyc"))
        if cache_pyc:
            pyc_path = cache_pyc[0]
    
    # 2. 反编译
    ok_py = repro_file.parent / f"{repro_file.stem}OK.py"
    result = subprocess.run(
        ["python", "pycdc.py", str(pyc_path), "-o", str(ok_py)],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # 3. 检查编译
    compile_result = subprocess.run(
        ["python", "-m", "py_compile", str(ok_py)],
        capture_output=True,
        text=True,
        timeout=5
    )
    
    compile_ok = compile_result.returncode == 0
    error_msg = compile_result.stderr if compile_result.stderr else ""
    
    # 4. 字节码比较
    status = "UNKNOWN"
    if compile_ok:
        cmp_result = subprocess.run(
            ["python", "scripts/pyc_batch_verify.py", "single", str(pyc_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = cmp_result.stdout
        if "match_rate: 100.00%" in output:
            status = "NO-DEFECT"
        elif "match_rate:" in output:
            status = "DEFECT-REPRO"
        elif "decompile_status: failed" in output:
            status = "ERROR"
    
    results.append({
        'index': i,
        'filename': repro_file.name,
        'status': status,
        'compile_ok': compile_ok,
        'error': error_msg[:100] if error_msg else ""
    })
    
    print(f"{i:2d}. {repro_file.name:45s} | {status:15s} | compile={compile_ok}")

# 统计
total = len(results)
no_defect = sum(1 for r in results if r['status'] == "NO-DEFECT")
defect = sum(1 for r in results if r['status'] == "DEFECT-REPRO")
error = sum(1 for r in results if r['status'] == "ERROR")
unknown = total - no_defect - defect - error

print(f"\n统计: {total} 总计 | {no_defect} NO-DEFECT | {defect} DEFECT-REPRO | {error} ERROR | {unknown} UNKNOWN")

# 保存结果
summary_path = repro_dir / "verify_summary.txt"
with open(summary_path, 'w', encoding='utf-8') as f:
    f.write(f"""复现实例验证结果 - Round 61
总计: {total}
NO-DEFECT: {no_defect}
DEFECT-REPRO: {defect}
ERROR: {error}
UNKNOWN: {unknown}

详细结果:
""")
    for r in results:
        f.write(f"{r['index']:2d}. {r['filename']:45s} | {r['status']:15s} | compile={r['compile_ok']}\n")
        if r['error']:
            f.write(f"     Error: {r['error']}\n")

print(f"\n结果已保存至: {summary_path}")