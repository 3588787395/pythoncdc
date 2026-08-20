"""Compile and test all minimal repros for round 11."""
import sys, os, subprocess
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

repro_dir = os.path.join('.trae', 'specs', 'decompiler-test-comprehensive-10rounds', 'rounds', 'round_11', 'test_engineer', 'minimal_repros')

# Get all .py files
py_files = sorted([f for f in os.listdir(repro_dir) if f.endswith('.py') and not f.endswith('_decompiled.py')])
print(f"Found {len(py_files)} repro files")

results = []
for py_file in py_files:
    name = py_file.replace('.py', '')
    py_path = os.path.join(repro_dir, py_file)
    pyc_path = os.path.join(repro_dir, name + '.pyc')
    out_path = os.path.join(repro_dir, name + '_decompiled.py')
    
    # Compile
    try:
        import py_compile
        py_compile.compile(py_path, pyc_path, doraise=True)
        print(f'{name}: compiled OK')
    except Exception as e:
        print(f'{name}: compile FAILED: {e}')
        results.append((name, 'compile_error', str(e)))
        continue
    
    # Decompile
    try:
        result = subprocess.run(
            [sys.executable, 'pycdc.py', pyc_path, '-o', out_path],
            capture_output=True, text=True, timeout=60,
            cwd='f:/Downloads/pythoncdc-main'
        )
        if result.returncode != 0:
            print(f'{name}: decompile FAILED (exit {result.returncode})')
            results.append((name, 'decompile_error', result.stderr[:200]))
            continue
    except Exception as e:
        print(f'{name}: decompile exception: {e}')
        results.append((name, 'decompile_exception', str(e)))
        continue
    
    # Compare bytecode
    try:
        from compare_bytecode_v2 import compare_pyc_files
        result = compare_pyc_files(pyc_path, out_path)
        matched = result['matched']
        total = result['total_functions']
        rate = result['success_rate']
        status = 'PASS' if rate == 100.0 else 'FAIL'
        print(f'{name}: {status} ({matched}/{total} = {rate:.2f}%)')
        if result.get('mismatches'):
            for m in result['mismatches']:
                if 'error' in m:
                    print(f'  {m["function"]}: {m["error"]}')
                else:
                    print(f'  {m["function"]}: {m["total_diffs"]} diffs (orig={m.get("orig_count","?")} decomp={m.get("decomp_count","?")})')
        results.append((name, status, f'{matched}/{total}'))
    except Exception as e:
        print(f'{name}: compare exception: {e}')
        results.append((name, 'compare_error', str(e)))

print('\n=== Summary ===')
pass_count = sum(1 for _, s, _ in results if s == 'PASS')
fail_count = sum(1 for _, s, _ in results if s == 'FAIL')
error_count = sum(1 for _, s, _ in results if 'error' in s or 'exception' in s)
print(f'PASS: {pass_count}/{len(results)}')
print(f'FAIL: {fail_count}/{len(results)}')
print(f'ERROR: {error_count}/{len(results)}')
for name, status, detail in results:
    print(f'  {name}: {status} ({detail})')
