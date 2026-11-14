# rr-v5r163 零触碰矩阵：用当前树重解 r161c / r162 各案，与改前基线产物逐字节对比
#   r161c: not_or / nottail / nottail3 / ggo -> <name>_headprobe_out.py ; fused -> fused_out.py
#   r162 : cg1..cg9 -> <name>_out.py
# 逐案 SAME/DIFF -> EV/zerotouch_v163.txt
import os, subprocess

REPO = r'F:\Downloads\pythoncdc-main'
PY = r'D:/Python/python.exe'
EV = os.path.join(REPO, r'.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/mixcond')
R161 = r'D:/temp/opencode/cl_layout/r161c'
R162 = r'D:/temp/opencode/cl_layout/r162'
OUT = r'D:/temp/opencode/cl_layout/r163/zerotouch'

CASES = [
    (R161, 'not_or',   'not_or_headprobe_out.py'),
    (R161, 'nottail',  'nottail_headprobe_out.py'),
    (R161, 'nottail3', 'nottail3_headprobe_out.py'),
    (R161, 'ggo',      'ggo_headprobe_out.py'),
    (R161, 'fused',    'fused_out.py'),
    (R162, 'cg1_guard_then_ifelse',   'cg1_guard_then_ifelse_out.py'),
    (R162, 'cg2_guard_then_if',       'cg2_guard_then_if_out.py'),
    (R162, 'cg3_guard2_then_ifelse',  'cg3_guard2_then_ifelse_out.py'),
    (R162, 'cg4_real_add_handler',    'cg4_real_add_handler_out.py'),
    (R162, 'cg5_elif_continue',       'cg5_elif_continue_out.py'),
    (R162, 'cg6_control_plain_elif',  'cg6_control_plain_elif_out.py'),
    (R162, 'cg7_with_guard_then_ifelse', 'cg7_with_guard_then_ifelse_out.py'),
    (R162, 'cg8_with_guard_then_if',  'cg8_with_guard_then_if_out.py'),
    (R162, 'cg9_try_guard_then_ifelse', 'cg9_try_guard_then_ifelse_out.py'),
]

os.makedirs(OUT, exist_ok=True)
lines = []
n_same = n_diff = 0
for d, name, baseline in CASES:
    pyc = os.path.join(d, name + '.pyc')
    base = os.path.join(d, baseline)
    prod = os.path.join(OUT, name + '.py')
    if not os.path.isfile(pyc):
        lines.append('%-28s NO-PYC  %s' % (name, pyc)); continue
    if not os.path.isfile(base):
        lines.append('%-28s NO-BASELINE  %s' % (name, base)); continue
    if os.path.isfile(prod):
        os.remove(prod)
    r = subprocess.run([PY, '-I', '-X', 'utf8', os.path.join(REPO, 'pycdc.py'), pyc, '-o', prod],
                       capture_output=True, cwd=REPO, timeout=600)
    if not os.path.isfile(prod):
        lines.append('%-28s DECOMP-FAIL rc=%d' % (name, r.returncode)); n_diff += 1; continue
    a = open(base, 'rb').read()
    b = open(prod, 'rb').read()
    if a == b:
        n_same += 1
        lines.append('%-28s SAME   (%d bytes, baseline %s)' % (name, len(a), baseline))
    else:
        n_diff += 1
        al, bl = a.decode('utf-8', 'replace').splitlines(), b.decode('utf-8', 'replace').splitlines()
        first = next((i for i, (x, y) in enumerate(zip(al, bl), 1) if x != y),
                     min(len(al), len(bl)) + 1)
        lines.append('%-28s DIFF   (baseline %s, first diff line %d)' % (name, baseline, first))
        for i in range(max(0, first - 2), min(len(al), len(bl), first + 1)):
            lines.append('      base: %s' % al[i])
            lines.append('      curr: %s' % bl[i])

lines.append('')
lines.append('SAME %d / %d, DIFF %d' % (n_same, n_same + n_diff, n_diff))
text = '\n'.join(lines)
print(text)
with open(os.path.join(EV, 'zerotouch_v163.txt'), 'w', encoding='utf-8') as f:
    f.write(text + '\n')
