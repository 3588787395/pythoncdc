import sys, py_compile, subprocess, os
os.chdir(r'D:\temp\opencode')

cases = {
 'v1_and_earlyret': """def f(value):
    epoch = value or 0
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = f'got {epoch}'
    raise ValueError(msg)
""",
 'v2_and_plain': """def f(epoch):
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = f'got {epoch}'
    raise ValueError(msg)
""",
 'v3_single': """def f(epoch):
    if epoch >= 0:
        return epoch
    raise ValueError('neg')
""",
 'v4_and_tailcall': """def f(epoch):
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    return helper(epoch)
""",
 'v5_and_tailstore': """def f(epoch):
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = 'bad'
    sink(msg)
""",
 'v6_or_cond': """def f(value, epoch):
    if value or epoch:
        return epoch
    raise ValueError('neg')
""",
}

for name, src in cases.items():
    open(f'{name}.py', 'w', encoding='utf-8').write(src)
    py_compile.compile(f'{name}.py', cfile=f'{name}.pyc', doraise=True)
    subprocess.run([sys.executable, '-X', 'utf8', r'F:\Downloads\pythoncdc-main\pycdc.py',
                    f'{name}.pyc', '-o', f'{name}_out.py'], capture_output=True, text=True)
    out = open(f'{name}_out.py', encoding='utf-8').read()
    body = [l for l in out.split('\n') if l.strip() and not l.startswith('#')]
    has_raise = 'raise' in out
    has_tail = ('msg' in out and 'raise' in out) or ('return helper' in out) or ('sink' in out)
    print(f'--- {name}: raise_present={has_raise} tail_present={has_tail}')
    for l in body:
        print('   ', l)
