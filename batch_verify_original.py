"""Batch test: decompile all ORIGINAL pyc files (excluding __pycache__ and OK files)."""
import sys, os, marshal, dis, json, time

sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
os.chdir('f:/Downloads/pythoncdc-main')
from pycdc import decompile_pyc

def load_code_from_pyc(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.load(f)

def compare_code_objects(orig_code, decomp_code):
    if orig_code.co_code != decomp_code.co_code:
        return False
    if orig_code.co_exceptiontable != decomp_code.co_exceptiontable:
        return False
    orig_funcs = [c for c in orig_code.co_consts if hasattr(c, 'co_code')]
    decomp_funcs = [c for c in decomp_code.co_consts if hasattr(c, 'co_code')]
    if len(orig_funcs) != len(decomp_funcs):
        return False
    for of, df in zip(orig_funcs, decomp_funcs):
        if not compare_code_objects(of, df):
            return False
    return True

# Find all .pyc files, excluding __pycache__ and OK files
pyc_files = []
for root, dirs, files in os.walk('site-packages'):
    if '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.pyc') and 'OK' not in f:
            pyc_files.append(os.path.join(root, f))

print(f"Found {len(pyc_files)} original .pyc files (excluding __pycache__ and OK files)")

# Test each
results = {'pass': 0, 'fail': 0, 'error': 0, 'details': []}
start = time.time()

for i, pyc_path in enumerate(pyc_files):
    if time.time() - start > 250:
        print(f"Timeout reached at {i}/{len(pyc_files)}")
        break
    
    try:
        orig_code = load_code_from_pyc(pyc_path)
        decomp_source = decompile_pyc(pyc_path)
        
        # Strip header
        lines = decomp_source.split('\n')
        while lines and (lines[0].startswith('#') or lines[0].strip() == ''):
            lines.pop(0)
        decomp_source = '\n'.join(lines)
        
        decomp_code = compile(decomp_source, '<decompiled>', 'exec')
        
        if compare_code_objects(orig_code, decomp_code):
            results['pass'] += 1
            # Generate OK file
            ok_path = pyc_path.replace('.pyc', 'OK.py')
            with open(ok_path, 'w', encoding='utf-8') as f:
                f.write('# Source Generated with Decompyle++ (Python version)\n')
                f.write(f'# File: {os.path.basename(pyc_path)} (Python 3.11)\n\n')
                f.write(decomp_source)
        else:
            results['fail'] += 1
            results['details'].append(f"FAIL: {pyc_path}")
            
    except Exception as e:
        results['error'] += 1
        results['details'].append(f"ERROR: {pyc_path}: {str(e)[:100]}")

total = results['pass'] + results['fail'] + results['error']
print(f"\n=== RESULTS: {total} tested ===")
print(f"  PASS: {results['pass']}")
print(f"  FAIL: {results['fail']}")
print(f"  ERROR: {results['error']}")
if total > 0:
    print(f"  Success rate: {results['pass']/total*100:.1f}%")

print(f"\n=== FAILURES (first 50) ===")
for d in results['details'][:50]:
    print(f"  {d}")
