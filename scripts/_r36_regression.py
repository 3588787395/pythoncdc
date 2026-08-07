import sys, glob
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
from scripts.pyc_batch_verify import decompile_single, bytecode_diff

pycs = sorted(glob.glob('site-packages/**/*.pyc', recursive=True))[:30]
ok=0; partial=0; fail=0; total_rate=0; n=0
for pyc in pycs:
    r = decompile_single(pyc)
    if not r['success']:
        fail+=1
        print(f'{pyc}: FAIL')
        continue
    d = bytecode_diff(pyc, r['ok_py_path'])
    if d['match_rate']==1.0:
        ok+=1
    else:
        partial+=1
    total_rate += d['match_rate']
    n+=1
    if d['match_rate']<1.0:
        print(f'{pyc}: {d["match_rate"]:.4f} ({d["matched_functions"]}/{d["total_functions"]})')
print(f'\nOK={ok} Partial={partial} Fail={fail} Avg={total_rate/n:.4f}')
