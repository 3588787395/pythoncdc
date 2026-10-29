# Varargs variant matrix: annotated / unannotated / mixed / defaults / kwonly.
import sys, py_compile, subprocess, os
os.chdir(r'D:\temp\opencode')

cases = {
 'va1_annotated': """from __future__ import annotations
def f(*args: object, **kwargs: object) -> object:
    return args
""",
 'va2_unannotated': """def f(*args, **kwargs):
    return args
""",
 'va3_mixed_pos_annotated': """def f(x: int, *rest: str, y: float = 1.0, **opts: bool) -> None:
    pass
""",
 'va4_kwonly_no_star_args': """def f(x: int, *, sep: str = ' ') -> None:
    pass
""",
 'va5_defaults_vararg': """def f(a=1, *args, b=2, **kw):
    pass
""",
 'va6_pep563_unpack': """from __future__ import annotations
def f(self, **kwargs: Unpack[V]) -> Self:
    pass
""",
 'va7_lambda_default': """g = lambda x, y=2: x + y
""",
 'va8_posonly': """def f(a, b, /, c: int = 3, *rest: bytes, d: str, **kw: float) -> str:
    return ''
""",
}

for name, src in cases.items():
    open(f'{name}.py', 'w', encoding='utf-8').write(src)
    py_compile.compile(f'{name}.py', cfile=f'{name}.pyc', doraise=True)
    r = subprocess.run([sys.executable, '-X', 'utf8', r'F:\Downloads\pythoncdc-main\pycdc.py',
                        f'{name}.pyc', '-o', f'{name}_out.py'], capture_output=True, text=True)
    out = open(f'{name}_out.py', encoding='utf-8').read()
    sig = [l.strip() for l in out.split('\n') if l.strip().startswith(('def ', 'g = '))]
    print(f'--- {name}: rc={r.returncode}')
    for s in sig:
        print('   ', s)
    if r.stderr.strip():
        print('    STDERR:', r.stderr.strip()[:200])
