import os, subprocess, sys

repro_dir = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros'
passed = 0
failed = 0
results = []

for f in sorted(os.listdir(repro_dir)):
    if not f.endswith('.pyc'):
        continue
    name = f.replace('.pyc', '')
    pyc_path = os.path.join(repro_dir, f)
    py_path = os.path.join(repro_dir, name + '.py')
    out_path = os.path.join(repro_dir, name + '_decompiled.py')
    
    # Run decompiler
    result = subprocess.run([sys.executable, 'pycdc.py', pyc_path, '-o', out_path], 
                          capture_output=True, text=True, cwd='.')
    
    if not os.path.exists(out_path):
        results.append((name, 'FAIL', 'No output'))
        failed += 1
        continue
    
    # Compare using compare_bytecode_v2
    result2 = subprocess.run([sys.executable, 'compare_bytecode_v2.py', pyc_path, out_path],
                           capture_output=True, text=True, cwd='.')
    
    output = result2.stdout + result2.stderr
    if 'Matched: ' in output:
        # Extract success rate
        for line in output.split('\n'):
            if 'Success rate:' in line:
                rate = line.strip()
                if '100.00%' in line:
                    results.append((name, 'PASS', rate))
                    passed += 1
                else:
                    results.append((name, 'FAIL', rate))
                    failed += 1
                break
    else:
        results.append((name, 'ERROR', output[:100]))
        failed += 1

print(f'\nResults: {passed}/{passed+failed} passed')
for name, status, info in results:
    print(f'  {status:4s} {name}: {info}')
