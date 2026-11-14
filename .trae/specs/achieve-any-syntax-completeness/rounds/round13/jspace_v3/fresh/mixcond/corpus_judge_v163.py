# rr-v5r163 五语料判官（request/tarfile/cookiejar/subprocess/difflib）
# 每案：pycdc.py <pyc> -o D:/temp/opencode/cl_layout/r163/judge/<name>.py
#       scripts/pyc_verify.py single <pyc> --source <product>
# 读数与失败名单 -> EV/corpus_judge_v163.txt
import os, subprocess

REPO = r'F:\Downloads\pythoncdc-main'
PY = r'D:/Python/python.exe'
EV = os.path.join(REPO, r'.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/mixcond')
JD = r'D:/temp/opencode/cl_layout/r163/judge'

CORPORA = [
    ('request',    r'D:/Python/Lib/urllib/__pycache__/request.cpython-311.pyc'),
    ('tarfile',    r'D:/Python/Lib/__pycache__/tarfile.cpython-311.pyc'),
    ('cookiejar',  r'D:/Python/Lib/http/__pycache__/cookiejar.cpython-311.pyc'),
    ('subprocess', r'D:/Python/Lib/__pycache__/subprocess.cpython-311.pyc'),
    ('difflib',    r'D:/Temp/opencode/cl_layout/r147diag/difflib_orig.pyc'),
]

os.makedirs(JD, exist_ok=True)
lines = []
for name, orig in CORPORA:
    if not os.path.isfile(orig):
        lines.append('%s: ORIG-MISSING %s' % (name, orig))
        continue
    prod = os.path.join(JD, name + '.py')
    if os.path.isfile(prod):
        os.remove(prod)
    d = subprocess.run([PY, '-I', '-X', 'utf8', os.path.join(REPO, 'pycdc.py'), orig, '-o', prod],
                       capture_output=True, cwd=REPO, timeout=1800)
    if not os.path.isfile(prod):
        lines.append('%s: DECOMP-FAIL rc=%d %s' % (name, d.returncode,
                     (d.stderr or b'').decode('utf-8', 'replace')[:300].replace('\n', ' ')))
        continue
    v = subprocess.run([PY, '-I', '-X', 'utf8', os.path.join(REPO, 'scripts/pyc_verify.py'),
                        'single', orig, '--source', prod],
                       capture_output=True, cwd=REPO, timeout=3600)
    out = ((v.stdout or b'') + (v.stderr or b'')).decode('utf-8', 'replace')
    stat = [l.strip() for l in out.splitlines() if 'status=' in l]
    fails = [l.strip() for l in out.splitlines()
             if l.strip().startswith('***') or 'Failure' in l]
    lines.append('%s: %s' % (name, stat[0] if stat else 'NO-STATUS rc=%d' % v.returncode))
    for f in fails:
        lines.append('    - %s' % f)
    lines.append('')

text = '\n'.join(lines)
print(text)
with open(os.path.join(EV, 'corpus_judge_v163.txt'), 'w', encoding='utf-8') as f:
    f.write(text + '\n')
