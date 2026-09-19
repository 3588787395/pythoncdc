"""R4-G probe 4: map which shapes make the decompiler drop code after a boolop."""
import os
import subprocess
import py_compile
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
PY3 = r'D:\Python\python.exe'
OUT = os.path.join(ROOT, '_r4_tmp', 'gen4')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, ROOT)

CASES = {
    'm0_or_then_if_flag': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    if self.flag:
        return 1
    else:
        return 2
""",
    'm1_or_then_call_then_if': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    self.foo(op)
    if self.flag:
        return 1
    else:
        return 2
""",
    'm2_or_then_call_only': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    self.foo(op)
    return op
""",
    'm3_or_assign_plain_ifelse': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2
""",
    'm4_or_assign_noelse': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    return op
""",
    'm5_or_assign_only': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    return op, user
""",
    'm6_and_variant': """
def f(self):
    ok = self.a() and self.b()
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2
""",
    'm7_or_assign_attr_target': """
def f(self):
    self.op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2
""",
    'm8_or_assign_subscr': """
def f(self):
    d = {}
    d['k'] = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2
""",
    'm9_or_assign_while': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    while user:
        user = self.step()
    return op
""",
    'm10_or_assign_for': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    for x in user:
        print(x)
    return op
""",
    'm11_or_expr_stmt': """
def f(self):
    self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2
""",
    'm12_or_assign_try': """
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    try:
        self.foo(user)
    except Exception:
        pass
    return op
""",
}


def run(name, src):
    p = os.path.join(OUT, name + '.py')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(src.lstrip('\n'))
    pyc = p[:-3] + '.pyc'
    py_compile.compile(p, cfile=pyc, doraise=True)
    r = subprocess.run([PY3, os.path.join(ROOT, 'pycdc.py'), '--region', pyc],
                       capture_output=True, text=True, timeout=120, cwd=ROOT)
    body = [l for l in r.stdout.split('\n') if l.strip() and not l.lstrip().startswith('#')]
    n_stmt = len([l for l in body if l.strip() != 'def f(self):'])
    # count non-empty source statements (approx): lines ending with ':' or starting with return
    src_lines = [l for l in src.strip().split('\n')[1:] if l.strip()]
    bad = n_stmt < len(src_lines) - 4  # rough
    return n_stmt, body, bad


def main():
    print('%-28s %6s %6s  %s' % ('case', 'srcLn', 'outLn', 'status'))
    for name, src in CASES.items():
        src_lines = [l for l in src.strip().split('\n')[1:] if l.strip()]
        try:
            n, body, bad = run(name, src)
        except Exception as e:
            print('%-28s ERROR %s' % (name, e))
            continue
        status = 'DROPPED' if bad else 'ok'
        print('%-28s %6d %6d  %s' % (name, len(src_lines), n, status))
        if bad:
            print('      out:', ' | '.join(l.strip() for l in body))


if __name__ == '__main__':
    main()
