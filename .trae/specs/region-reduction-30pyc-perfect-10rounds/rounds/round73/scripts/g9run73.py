# -*- coding: utf-8 -*-
"""Round 73 G9 synth gate: build the synth target list, decompile under both arms
(prev = R72 landed bytes mirror, landed = R73 worktree), run the mandated ruler on
both products, and write logs/G9_synth_r73.txt."""
import io
import json
import os
import py_compile
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
C = r'D:/Temp/opencode/r73gate/center'
G = os.path.join(C, 'logs')
D = os.path.join(C, 'dump')
RT = r'D:/Temp/opencode/r73gate'
R72 = r'D:/Temp/opencode/r72gate'
REPO = r'F:/Downloads/pythoncdc-main'
os.makedirs(G, exist_ok=True)
os.makedirs(D, exist_ok=True)

# --- new F-PAD synth (round73 fix1 shape): then-arm early returns, no source-level else ---
pad_src = r'''# -*- coding: utf-8 -*-
def pad_a(x, y):
    if not isinstance(x, int):
        return None
    elif isinstance(y, str):
        if y:
            return y.upper()


def pad_b(x, y):
    if not isinstance(x, int):
        return None
    elif isinstance(y, str):
        return y.strip()
    return None


def pad_c(x, y, bag):
    if not isinstance(x, int):
        return None
    elif isinstance(y, str):
        bag[y] = x
        return None
    return len(bag)


def pad_d(x, y, bag):
    if not isinstance(x, int):
        return None
    elif isinstance(y, str):
        if y.startswith('a'):
            bag.append(y)
            return None
        bag.append(y.lower())
'''
sy = os.path.join(C, 'synth')
os.makedirs(sy, exist_ok=True)
io.open(os.path.join(sy, 'pad73_shapes.py'), 'w', encoding='utf-8', newline='\n').write(pad_src)
py_compile.compile(os.path.join(sy, 'pad73_shapes.py'),
                   cfile=os.path.join(sy, 'pad73_shapes.pyc'), doraise=True)

# --- fix3 synth: compile the sources to sibling .pyc ---
for n in ('assert_or_tail.py', 'polarity_andor.py'):
    s = os.path.join(RT, 'fix3', 'synth', n)
    if os.path.isfile(s):
        py_compile.compile(s, cfile=s[:-3] + '.pyc', doraise=True)

# --- target list ---
paths = []
for root in (os.path.join(R72, 'diag1', 'synth', 'out'),
             os.path.join(RT, 'diag1', 'synth', 'out'),
             os.path.join(RT, 'fix2', 'synth'),
             os.path.join(RT, 'fix3', 'synth'),
             sy):
    if not os.path.isdir(root):
        continue
    for f in sorted(os.listdir(root)):
        if f.endswith('.pyc') and '__pycache__' not in root:
            paths.append(os.path.join(root, f).replace('\\', '/'))
paths = sorted(set(paths))
lp = os.path.join(D, 'synth73.txt')
io.open(lp, 'w', encoding='utf-8', newline='\n').write('\n'.join(paths) + '\n')
print('synth targets:', len(paths))

# --- official readings per arm (h62 run) ---
h62 = os.path.join(C, 'h62.py')
for arm in ('prev', 'landed'):
    out = os.path.join(D, '%s_synth73_r73.jsonl' % arm)
    have = sum(1 for l in io.open(out, encoding='utf-8') if l.strip()) if os.path.isfile(out) else 0
    if have == len(paths):
        print('official %s: %d rows (cached)' % (arm, have))
        continue
    if os.path.isfile(out):
        os.remove(out)
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', h62,
                        'run', '--arm=%s' % arm, '--list=%s' % lp, '--out=%s' % out],
                       capture_output=True, text=True)
    io.open(os.path.join(D, 'g9_h62_%s.txt' % arm), 'w', encoding='utf-8',
            newline='\n').write(r.stdout + '\n' + r.stderr)
    n = sum(1 for l in io.open(out, encoding='utf-8') if l.strip()) if os.path.isfile(out) else 0
    print('official %s: %d rows' % (arm, n))

# --- mandated readings per arm (pyc_verify batch over the arm product) ---
def mangled(p):
    rel = p.replace('\\', '/')
    r0 = REPO.replace('\\', '/') + '/site-packages/'
    if rel.startswith(r0):
        rel = rel[len(r0):]
    return os.path.join(C, 'build_' + ARM,
                        rel.replace('/', '__')[:-4].replace(':', '_') + 'OK.py').replace('\\', '/')


for ARM in ('prev', 'landed'):
    idx = []
    miss = []
    for p in paths:
        d = mangled(p)
        if os.path.isfile(d):
            idx.append({'path': p, 'source': d})
        else:
            miss.append(p)
    ij = os.path.join(D, 'synth_idx_%s.json' % ARM)
    io.open(ij, 'w', encoding='utf-8', newline='\n').write(json.dumps(idx, ensure_ascii=False, indent=1))
    outj = os.path.join(D, 'mand_synth_%s_r73.json' % ARM)
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8',
                        os.path.join(REPO, 'scripts', 'pyc_verify.py'), 'batch',
                        '--index', ij, '--json', outj], capture_output=True, text=True)
    io.open(os.path.join(D, 'g9_mand_%s.txt' % ARM), 'w', encoding='utf-8',
            newline='\n').write(r.stdout + '\n' + r.stderr)
    print('mandated %s: missing-products=%d' % (ARM, len(miss)))

# --- G9 verdict ---
A = json.load(io.open(os.path.join(D, 'mand_synth_prev_r73.json'), encoding='utf-8'))
B = json.load(io.open(os.path.join(D, 'mand_synth_landed_r73.json'), encoding='utf-8'))
ao = {r['pyc']: r for r in A['rows']}
bo = {r['pyc']: r for r in B['rows']}
L = ['G9 synth gate: mandated status prev(R72 bytes) -> landed(R73 bytes)', '=' * 70]
tally = {'IMPROVED': 0, 'REGRESSED': 0, 'SAME': 0}
for k in sorted(set(ao) | set(bo)):
    a, b = ao.get(k), bo.get(k)
    if not a or not b:
        tally['SAME'] += 0
        L.append('%-46s MISSING-IN-%s' % (os.path.basename(k), 'prev' if not a else 'landed'))
        continue
    same = (a['status'], a['units_success'], a['units_total']) == \
           (b['status'], b['units_success'], b['units_total'])
    if a['status'] != b['status']:
        v = 'IMPROVED' if a['status'] != 'success' and b['status'] == 'success' else 'REGRESSED'
    elif a['units_success'] != b['units_success']:
        v = 'IMPROVED' if b['units_success'] > a['units_success'] else 'REGRESSED'
    else:
        v = 'SAME'
    tally[v] += 1
    L.append('%-46s status=%-8s units=%d/%d success_rate=%s -> status=%-8s units=%d/%d success_rate=%s %s'
             % (os.path.basename(k), a['status'], a['units_success'], a['units_total'],
                ('%.2f%%' % (100 * a['success_rate'])) if a['success_rate'] is not None else '-',
                b['status'], b['units_success'], b['units_total'],
                ('%.2f%%' % (100 * b['success_rate'])) if b['success_rate'] is not None else '-',
                v))
L += ['', 'IMPROVED=%d REGRESSED=%d SAME=%d' % (tally['IMPROVED'], tally['REGRESSED'], tally['SAME']),
      'G9 verdict: %s' % ('PASS' if tally['REGRESSED'] == 0 else 'FAIL')]
io.open(os.path.join(G, 'G9_synth_r73.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
print(L[-2]); print(L[-1])
