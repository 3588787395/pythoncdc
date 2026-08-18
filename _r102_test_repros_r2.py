#!/usr/bin/env python3
"""Round 02 批量测试最小复现实例"""
import os, sys, subprocess
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
os.chdir(project_root)
from compare_bytecode_v2 import compare_pyc_files

repro_dir = os.path.join(project_root, '.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_02', 'test_engineer', 'minimal_repros')

results = []
for fname in sorted(os.listdir(repro_dir)):
    if not fname.endswith('.py') or '_decompiled' in fname:
        continue
    py_path = os.path.join(repro_dir, fname)
    pyc_path = py_path.replace('.py', '.pyc')
    decomp_path = py_path.replace('.py', '_decompiled.py')
    subprocess.run([sys.executable, '-c', f"import py_compile; py_compile.compile(r'{py_path}', r'{pyc_path}', doraise=True)"], timeout=30)
    r = subprocess.run([sys.executable, 'pycdc.py', pyc_path, '-o', decomp_path], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        results.append((fname, 'DECOMPILE_FAIL', 0, 0))
        continue
    result = compare_pyc_files(pyc_path, decomp_path)
    results.append((fname, 'OK' if result['success_rate'] == 100 else 'MISMATCH', result['matched'], result['total_functions']))

print(f"\n{'='*80}")
print(f"Minimal Repro Test Results (Round 02)")
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
