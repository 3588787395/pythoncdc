import py_compile, sys, os, dis, io
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = sorted([f for f in os.listdir(HERE) if f.startswith('test_p') and f.endswith('.py')])

bc_match = 0
bc_mismatch = 0
bc_error = 0
mismatches = []
errors = []

for tf in TESTS:
    pyc_path = os.path.join(HERE, tf + 'c')
    test_path = os.path.join(HERE, tf)
    try:
        py_compile.compile(test_path, cfile=pyc_path, doraise=True)
        src = decompile_pyc(pyc_path)
        
        with open(test_path) as f:
            original_code = compile(f.read(), tf, 'exec')
        decompiled_code = compile(src, '<decomp>', 'exec')
        
        orig_func = original_code.co_consts[0]
        deco_func = decompiled_code.co_consts[0]
        
        if orig_func.co_code == deco_func.co_code:
            bc_match += 1
        else:
            bc_mismatch += 1
            mismatches.append((tf, len(orig_func.co_code), len(deco_func.co_code)))
            
    except SyntaxError as e:
        bc_error += 1
        errors.append(f'{tf}: SYNTAX - {e}')
    except Exception as e:
        bc_error += 1
        errors.append(f'{tf}: ERROR - {e}')
    finally:
        if os.path.exists(pyc_path):
            os.remove(pyc_path)

result = f'Bytecode: MATCH={bc_match}, MISMATCH={bc_mismatch}, ERROR={bc_error}, Total={len(TESTS)}\n'
result += f'Match rate: {bc_match}/{len(TESTS)} = {bc_match*100//len(TESTS)}%\n'
if mismatches:
    result += f'\nMismatches ({len(mismatches)}):\n'
    for name, olen, dlen in mismatches:
        result += f'  {name}: {olen}orig vs {dlen}deco\n'
if errors:
    result += f'\nErrors:\n'
    for e in errors:
        result += f'  {e}\n'
print(result)
with open(os.path.join(HERE, 'bc_results.txt'), 'w') as f:
    f.write(result)
