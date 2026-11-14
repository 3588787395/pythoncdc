# repro_cg7.py: urlretrieve 形（with 包裹 + 守卫 and + 后续 if/else）
import os, subprocess, py_compile

REPO = r'F:\Downloads\pythoncdc-main'
PY = r'D:/Python/python.exe'
D = r'D:\temp\opencode\cl_layout\r162'

CASES = {
    'cg7_with_guard_then_ifelse': """def f(url_type, filename):
    with closing(open(url)) as fp:
        headers = fp.info()
        if url_type == 'file' and not filename:
            return 1
        if filename:
            tfp = open(filename, 'wb')
        else:
            tfp = tmpfile()
        return tfp
""",
    'cg8_with_guard_then_if': """def f(url_type, filename):
    with closing(open(url)) as fp:
        if url_type == 'file' and not filename:
            return 1
        if filename:
            tfp = 2
        return tfp
""",
    'cg9_try_guard_then_ifelse': """def f(url_type, filename):
    try:
        if url_type == 'file' and not filename:
            return 1
        if filename:
            tfp = 2
        else:
            tfp = 3
        return tfp
    except ValueError:
        pass
""",
}

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
        print('\n'.join(open(out, encoding='utf-8').read().splitlines()[3:]))
    else:
        print('DECOMP FAIL rc=%s %s' % (r.returncode, r.stderr.decode('utf-8', 'replace')[:300]))
