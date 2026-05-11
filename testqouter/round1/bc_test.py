import py_compile, sys, os, dis

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from pycdc import decompile_pyc

TESTS = sorted([f for f in os.listdir(HERE) if f.startswith('test_') and f.endswith('.py')])

from dis import get_instructions

def normalize_bytecode(code_obj):
    normalized = []
    for instr in get_instructions(code_obj):
        op = instr.opname
        if op.startswith('CACHE'):
            continue
        normalized.append(op)
    return tuple(normalized)

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
        
        orig_norm = normalize_bytecode(orig_func)
        deco_norm = normalize_bytecode(deco_func)
        
        if orig_norm == deco_norm:
            bc_match += 1
        else:
            bc_mismatch += 1
            mismatches.append(tf)
            
    except SyntaxError as e:
        bc_error += 1
        errors.append(f'{tf}: SYNTAX - {e}')
    except Exception as e:
        bc_error += 1
        errors.append(f'{tf}: {e}')
    finally:
        if os.path.exists(pyc_path):
            os.remove(pyc_path)

result = f'Bytecode: MATCH={bc_match}, MISMATCH={bc_mismatch}, ERROR={bc_error}, Total={len(TESTS)}\n'
result += f'Bytecode match rate: {bc_match}/{len(TESTS)} = {bc_match*100//len(TESTS)}%\n'
if mismatches:
    result += f'\nMismatched ({len(mismatches)}):\n'
    for m in mismatches:
        result += f'  {m}\n'
if errors:
    result += f'\nErrors ({len(errors)}):\n'
    for e in errors:
        result += f'  {e}\n'

print(result)
with open(os.path.join(HERE, 'bc_results.txt'), 'w') as f:
    f.write(result)
