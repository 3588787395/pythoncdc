import sys, os, warnings, json
warnings.filterwarnings('ignore')
sys.path.insert(0, '.')
from pycdc import decompile_pyc

sp = 'site-packages'
pyc_files = []
for root, dirs, files in os.walk(sp):
    for f in files:
        if f.endswith('.pyc'):
            pyc_files.append(os.path.join(root, f))

print(f'Total: {len(pyc_files)}', flush=True)

ok = 0
fail = 0
failed_list = []
for i, pyc in enumerate(pyc_files):
    try:
        src = decompile_pyc(pyc)
        if src:
            try:
                compile(src, '<d>', 'exec')
                ok += 1
            except SyntaxError:
                fail += 1
                failed_list.append(pyc)
        else:
            fail += 1
            failed_list.append(pyc)
    except Exception:
        fail += 1
        failed_list.append(pyc)
    if (i + 1) % 200 == 0:
        print(f'{i+1}/{len(pyc_files)} ok={ok} f={fail}', flush=True)

print(f'RESULT: {ok}/{len(pyc_files)} ok, {fail} fail', flush=True)
if failed_list:
    print('FAILED:', flush=True)
    for f in failed_list[:30]:
        print(f'  {f}', flush=True)
