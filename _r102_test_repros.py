#!/usr/bin/env python3
"""批量测试最小复现实例的反编译字节码一致性"""
import os
import sys
import subprocess

# 确保能找到项目模块
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.chdir(project_root)

from compare_bytecode_v2 import compare_pyc_files

repro_dir = os.path.join(project_root, '.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_01', 'test_engineer', 'minimal_repros')

results = []
for fname in sorted(os.listdir(repro_dir)):
    if not fname.endswith('.py'):
        continue
    if '_decompiled' in fname:
        continue
    py_path = os.path.join(repro_dir, fname)
    pyc_path = py_path.replace('.py', '.pyc')
    decomp_path = py_path.replace('.py', '_decompiled.py')
    
    # 反编译
    cmd = [sys.executable, 'pycdc.py', pyc_path, '-o', decomp_path]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    if r.returncode != 0:
        results.append((fname, 'DECOMPILE_FAIL', 0, 0))
        continue
    
    # 比较字节码
    result = compare_pyc_files(pyc_path, decomp_path)
    results.append((fname, 'OK' if result['success_rate'] == 100 else 'MISMATCH', result['matched'], result['total_functions']))

print(f"\n{'='*80}")
print(f"Minimal Repro Test Results (Round 01)")
print(f"{'='*80}")
passed = 0
total = len(results)
for fname, status, matched, total_funcs in results:
    symbol = '[PASS]' if status == 'OK' else '[FAIL]'
    print(f"  {symbol} {fname}: {status} ({matched}/{total_funcs})")
    if status == 'OK':
        passed += 1
print(f"\nPassed: {passed}/{total}")
print(f"Success rate: {passed/total*100:.1f}%")
