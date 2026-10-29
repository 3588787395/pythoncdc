# Early-return polarity inversion repro family (REAL46-003 _c3_merge shape).
# v1: while True + purge + early return + loop body after guard.
import sys, py_compile, subprocess, os
os.chdir(r'D:\temp\opencode')

v1 = '''\
def f(sequences):
    result = []
    while True:
        sequences = [s for s in sequences if s]
        if not sequences:
            return result
        for s1 in sequences:
            candidate = s1[0]
            for s2 in sequences:
                if candidate in s2[1:]:
                    candidate = None
                    break
            else:
                break
        if candidate is None:
            raise RuntimeError('Inconsistent hierarchy')
        result.append(candidate)
        for seq in sequences:
            if seq and seq[0] is candidate:
                del seq[0]
'''

# v2: no while loop - plain function with guard + body
v2 = '''\
def f(sequences):
    result = []
    if not sequences:
        return result
    for s1 in sequences:
        candidate = s1[0]
        result.append(candidate)
    return result
'''

# v3: while loop but guard at top (guard before any stmt)
v3 = '''\
def f(items):
    while True:
        if not items:
            return None
        items = items[1:]
        print(items)
'''

# v4: guard with plain local (no comprehension purge before)
v4 = '''\
def f(items):
    result = []
    while True:
        if not items:
            return result
        result.append(items[0])
        items = items[1:]
'''

for name, src in [('er1_c3merge', v1), ('er2_plainguard', v2),
                  ('er3_guardsimple', v3), ('er4_guardappend', v4)]:
    open(f'{name}.py', 'w', encoding='utf-8').write(src)
    py_compile.compile(f'{name}.py', cfile=f'{name}.pyc', doraise=True)
    r = subprocess.run([sys.executable, '-X', 'utf8', r'F:\Downloads\pythoncdc-main\pycdc.py',
                        f'{name}.pyc', '-o', f'{name}_out.py'], capture_output=True, text=True)
    out = open(f'{name}_out.py', encoding='utf-8').read()
    # polarity check: does product keep `if not ...: return` shape?
    grab = False
    body = []
    for l in out.split('\n'):
        if l.startswith('def f('):
            grab = True
        elif l.startswith('def ') and grab:
            break
        elif grab:
            body.append(l)
    has_not = any('if not ' in l for l in body)
    has_else = any(l.strip().startswith('else:') for l in body)
    print(f'--- {name}: rc={r.returncode} earlyret_not={has_not} else_branch={has_else}')
    for l in body:
        print('   |', l)
    print()
