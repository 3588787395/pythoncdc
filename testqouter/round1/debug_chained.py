import os, sys, py_compile, dis, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base import decompile_pyc, compile_and_compare, test_semantic_equivalence

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

test_name = 'test_r1_chained_compare'
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

try:
    compile(decompiled, '<decompiled>', 'exec')
    print('\n--- Syntax: OK ---')
except SyntaxError as e:
    print(f'\n--- Syntax: FAIL - {e} ---')

result = compile_and_compare(py_path, decompiled)
print(f'\n--- Bytecode Compare ---')
print(json.dumps(result, indent=2, default=str))

semantic = test_semantic_equivalence(py_path, decompiled)
print(f'\n--- Semantic ---')
print(json.dumps(semantic, indent=2, default=str))

if os.path.exists(pyc_path):
    os.remove(pyc_path)
