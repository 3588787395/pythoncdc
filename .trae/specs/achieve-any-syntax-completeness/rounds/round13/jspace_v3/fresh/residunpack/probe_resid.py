# probe_resid.py: which dual-unpack positions render wrong (RESIDUNPACK family)
import os, subprocess, py_compile

REPO = 'F:/Downloads/pythoncdc-main'
OUT = 'D:/temp/opencode/cl_layout/r153probe'
PY = 'D:/Python/python.exe'
os.makedirs(OUT, exist_ok=True)

CASES = {
    'R1_toplevel': """def f1(x, y):
    (a, b), (c, d) = x, y
    return a + b + c + d
""",
    'R2_whilebody': """def f2(pairs):
    total = 0
    while total < len(pairs):
        (a, b), (c, d) = pairs[total], pairs[total + 1]
        total += a + b + c + d
    return total
""",
    'R3_forbody': """def f3(pairs):
    out = []
    for p in pairs:
        (a, b), (c, d) = p, p
        out.append(a + b + c + d)
    return out
""",
    'R4_ifbody': """def f4(x, y):
    if x:
        (a, b), (c, d) = x, y
    return (a, b, c, d)
""",
    'R5_ifelse': """def f5(x, y):
    if x:
        t = 1
    else:
        t = 2
    (a, b), (c, d) = x, y
    return a + b + c + d + t
""",
    'R6_after_while': """def f6(xs):
    i = 0
    while i < len(xs):
        i += 1
    (a, b), (c, d) = xs[0], xs[1]
    return a + b + c + d
""",
}

for name, src in CASES.items():
    sp = os.path.join(OUT, name + '_src.py')
    open(sp, 'w', encoding='utf-8').write(src)
    pyc = os.path.join(OUT, name + '.pyc')
    py_compile.compile(sp, cfile=pyc, doraise=True)
    outp = os.path.join(OUT, name + '_out.py')
    r = subprocess.run([PY, '-I', '-X', 'utf8', REPO + '/pycdc.py', pyc, '-o', outp],
                       capture_output=True, cwd=REPO, timeout=180)
    prod = open(outp, encoding='utf-8').read() if os.path.isfile(outp) else '<DECOMP FAIL>'
    print('==== %s ====' % name)
    print('\n'.join(l for l in prod.splitlines() if not l.startswith('#')))
