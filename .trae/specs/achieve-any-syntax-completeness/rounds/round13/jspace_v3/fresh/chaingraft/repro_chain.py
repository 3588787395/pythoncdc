# repro_chain.py: r162 CHAINGRAFT 最小复现 —— 守卫 and + 后续 if/else 被熔成 if/elif
import os, subprocess, sys, py_compile

REPO = r'F:\Downloads\pythoncdc-main'
PY = r'D:/Python/python.exe'
D = r'D:\temp\opencode\cl_layout\r162'

CASES = {
    'cg1_guard_then_ifelse': """def f(url_type, filename):
    if url_type == 'file' and not filename:
        return 1
    if filename:
        tfp = open(filename, 'wb')
    else:
        tfp = tmpfile()
    return tfp
""",
    'cg2_guard_then_if': """def f(a, b):
    if a == 'x' and not b:
        return 1
    if b:
        c = 2
    return c
""",
    'cg3_guard2_then_ifelse': """def f(a, b, c):
    if a and b:
        return 1
    if c:
        d = 2
    else:
        d = 3
    return d
""",
    'cg4_real_add_handler': """def add_handler(protocol, condition):
    if condition.startswith('error'):
        kind = 0
    elif condition == 'open':
        kind = 1
    elif condition == 'response':
        kind = 2
    elif condition == 'request':
        kind = 3
    else:
        return None
    return kind
""",
    'cg5_elif_continue': """def add_handler(protocol, condition):
    for meth in ('a', 'b'):
        if condition.startswith('error'):
            kind = 0
        elif condition == 'open':
            kind = 1
        elif condition == 'response':
            kind = 2
        elif condition == 'request':
            kind = 3
        else:
            continue
        kind = kind + 1
    return None
""",
    'cg6_control_plain_elif': """def f(a, b):
    if a:
        x = 1
    elif b:
        x = 2
    else:
        x = 3
    return x
""",
}

os.makedirs(D, exist_ok=True)
for name, src in CASES.items():
    sp = os.path.join(D, name + '_src.py')
    pyc = os.path.join(D, name + '.pyc')
    out = os.path.join(D, name + '_out.py')
    open(sp, 'w', encoding='utf-8').write(src)
    py_compile.compile(sp, cfile=pyc, doraise=True)
    if os.path.isfile(out):
        os.remove(out)
    r = subprocess.run([PY, '-I', '-X', 'utf8', os.path.join(REPO, 'pycdc.py'), pyc, '-o', out],
                       capture_output=True, cwd=REPO, timeout=300)
    print('=' * 70)
    print('CASE', name)
    if os.path.isfile(out):
        txt = open(out, encoding='utf-8').read().splitlines()
        print('\n'.join(txt[3:]))
    else:
        print('DECOMP FAIL rc=%s %s' % (r.returncode, r.stderr.decode('utf-8', 'replace')[:300]))
