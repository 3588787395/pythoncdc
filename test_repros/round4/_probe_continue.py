"""R4-H probe: find the shape that makes a loop-header `continue` (JUMP_BACKWARD to
loop header) inside an if-branch get DROPPED entirely."""
import os
import subprocess
import py_compile
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
PY3 = r'D:\Python\python.exe'
OUT = os.path.join(ROOT, '_r4_tmp', 'gen6')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, ROOT)

CASES = {
    'p0_and_chain_two_inner_fors_continue': '''
FORBID = ('a', 'b')
BLACK = ('x', 'y')


def f(self, tree, re):
    for node in tree:
        if isinstance(node, int) and isinstance(node.value, str):
            for ca in FORBID:
                if re.search(ca, node.value):
                    return {'e': -1, 'i': ca}
            for ca in BLACK:
                if ca in node.value:
                    return {'e': -1, 'i': ca}
            continue
        if isinstance(node, str) and isinstance(node.func, str):
            return {'e': -1, 'i': 2}
    return {'e': 0, 'i': ''}
''',
    'p1_and_chain_one_inner_for_continue': '''
BLACK = ('x', 'y')


def f(self, tree):
    for node in tree:
        if isinstance(node, int) and isinstance(node.value, str):
            for ca in BLACK:
                if ca in node.value:
                    return {'e': -1, 'i': ca}
            continue
        if isinstance(node, str):
            return {'e': -1, 'i': 2}
    return {'e': 0, 'i': ''}
''',
    'p2_no_and_chain_two_inner_fors': '''
FORBID = ('a', 'b')
BLACK = ('x', 'y')


def f(self, tree, re):
    for node in tree:
        if isinstance(node, int):
            for ca in FORBID:
                if re.search(ca, node.value):
                    return {'e': -1, 'i': ca}
            for ca in BLACK:
                if ca in node.value:
                    return {'e': -1, 'i': ca}
            continue
        if isinstance(node, str):
            return {'e': -1, 'i': 2}
    return {'e': 0, 'i': ''}
''',
    'p3_single_if_continue': '''
def f(self, tree):
    for node in tree:
        if isinstance(node, int):
            continue
        if isinstance(node, str):
            return 2
    return 0
''',
    'p4_and_chain_continue': '''
def f(self, tree):
    for node in tree:
        if isinstance(node, int) and isinstance(node.value, str):
            continue
        if isinstance(node, str):
            return 2
    return 0
''',
}


def main():
    for name, src in CASES.items():
        p = os.path.join(OUT, name + '.py')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(src.lstrip('\n'))
        pyc = p[:-3] + '.pyc'
        py_compile.compile(p, cfile=pyc, doraise=True)
        r = subprocess.run([PY3, os.path.join(ROOT, 'pycdc.py'), '--region', pyc],
                           capture_output=True, text=True, timeout=120, cwd=ROOT)
        body = [l for l in r.stdout.split('\n') if l.strip() and not l.lstrip().startswith('#')]
        n_cont = sum(1 for l in body if l.strip() == 'continue')
        src_cont = sum(1 for l in src.split('\n') if l.strip() == 'continue')
        flag = 'CONTINUE-DROPPED' if n_cont < src_cont else 'ok'
        print('====', name, '->', flag, '(src continue=%d, out continue=%d)' % (src_cont, n_cont))
        for l in body:
            print('   ', l)


if __name__ == '__main__':
    main()
