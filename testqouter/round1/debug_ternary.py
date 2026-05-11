import os, sys, py_compile, dis, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base import decompile_pyc

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

test_name = 'test_r1_ternary_assign'
py_path = os.path.join(TEST_DIR, test_name + '.py')
pyc_path = py_path + 'c'

print('=' * 70)
print(f'TEST: {test_name}')
print('=' * 70)

with open(py_path, 'r', encoding='utf-8') as f:
    orig_source = f.read()
print('--- Original Source ---')
print(orig_source.strip())

py_compile.compile(py_path, pyc_path, doraise=True)

with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    f.read(12)
    code_obj = __import__('marshal').load(f)

print('\n--- Original Bytecode (inner function) ---')
for const in code_obj.co_consts:
    if hasattr(const, 'co_code'):
        dis.dis(const)

try:
    decompiled = decompile_pyc(pyc_path)
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'\n--- DECOMPILE FAILED: {e} ---')
    if os.path.exists(pyc_path):
        os.remove(pyc_path)
    sys.exit(1)

print('\n--- Decompiled Source ---')
print(decompiled)

if os.path.exists(pyc_path):
    os.remove(pyc_path)
