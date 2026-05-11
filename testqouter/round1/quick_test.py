import py_compile, sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.getcwd())))
sys.path.insert(0, '.')

TESTS = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]
print(f'Running {len(TESTS)} tests...')

statuses = {'PASS': 0, 'FAIL': 0, 'SYNTAX_ERROR': 0, 'DECOMP_ERROR': 0}
fails = []

for tf in sorted(TESTS):
    pyc_path = tf + 'c'
    try:
        py_compile.compile(tf, cfile=pyc_path, doraise=True)
        from pycdc import decompile_pyc
        src = decompile_pyc(pyc_path)
        try:
            compile(src, '<test>', 'exec')
            statuses['PASS'] += 1
        except SyntaxError as e:
            statuses['SYNTAX_ERROR'] += 1
            fails.append(f'{tf}: SYNTAX - {e}')
    except Exception as e:
        statuses['DECOMP_ERROR'] += 1
        fails.append(f'{tf}: DECOMP - {e}')
    finally:
        if os.path.exists(pyc_path):
            os.remove(pyc_path)

print(f'Results: PASS={statuses["PASS"]}, SYNTAX_ERROR={statuses["SYNTAX_ERROR"]}, DECOMP_ERROR={statuses["DECOMP_ERROR"]}, Total={len(TESTS)}')
print(f'Pass rate: {statuses["PASS"]}/{len(TESTS)} = {statuses["PASS"]*100//len(TESTS)}%')

if fails:
    print('\nFailures:')
    for f in fails:
        print(f'  {f}')
