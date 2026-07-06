#!/usr/bin/env python3
"""批量测试运行器 - 快速获取通过率"""
import py_compile, sys, os, json, dis

TEST_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(TEST_DIR))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, TEST_DIR)

from pycdc import decompile_pyc

def get_instructions(code):
    result = []
    for instr in dis.get_instructions(code):
        result.append((instr.opname, instr.argval, instr.argrepr))
    return result

def compare_bytecode(orig_insts, decomp_insts):
    jdiff, tdiff = 0, 0
    max_len = max(len(orig_insts), len(decomp_insts))
    for i in range(max_len):
        if i >= len(orig_insts) or i >= len(decomp_insts):
            tdiff += 1
        else:
            o = orig_insts[i]; d = decomp_insts[i]
            if o[0] != d[0]:
                if ('JUMP' in o[0] or 'JUMP' in d[0]):
                    jdiff += 1
                else:
                    tdiff += 1
            elif o[1] != d[1] and ('JUMP' in o[0] or 'JUMP' in d[0]):
                jdiff += 1
    return jdiff, tdiff

results = []
total, passed, failed, syntax_err, decomp_err, compile_err = 0, 0, 0, 0, 0, 0
semantic_ok = 0

files = sorted([f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')])

for f in files:
    total += 1
    name = f[:-3]
    py_path = os.path.join(TEST_DIR, f)
    pyc_path = os.path.join(TEST_DIR, f + 'c')
    
    try:
        # Compile original
        py_compile.compile(py_path, cfile=pyc_path, doraise=True)
        
        # Decompile
        try:
            src = decompile_pyc(pyc_path)
        except Exception as e:
            decomp_err += 1
            results.append({'name': name, 'status': 'DECOMP_ERROR', 'error': str(e)[:100]})
            continue
        
        # Syntax check
        try:
            compile(src, '<test>', 'exec')
        except SyntaxError as e:
            syntax_err += 1
            results.append({'name': name, 'status': 'SYNTAX_ERROR', 'error': str(e)[:100]})
            continue
        
        # Compare bytecode at module level
        orig_code = compile(open(py_path, encoding='utf-8').read(), py_path, 'exec')
        decomp_code = compile(src, '<decompiled>', 'exec')
        
        jdiff, tdiff = compare_bytecode(get_instructions(orig_code), get_instructions(decomp_code))
        
        if tdiff == 0 and jdiff == 0:
            status = 'PASS'
            passed += 1
        elif tdiff == 0:
            status = 'PASS_JUMP_DIFF'
            passed += 1
        else:
            status = 'FAIL'
            failed += 1
        
        results.append({
            'name': name, 'status': status,
            'jump_diffs': jdiff, 'true_diffs': tdiff
        })
        
    except Exception as e:
        compile_err += 1
        results.append({'name': name, 'status': 'COMPILE_ERROR', 'error': str(e)[:100]})
    finally:
        if os.path.exists(pyc_path):
            try: os.remove(pyc_path)
            except: pass

print(f"Total: {total}, Pass: {passed}, Fail: {failed}")
print(f"Decomp errors: {decomp_err}, Syntax errors: {syntax_err}, Compile errors: {compile_err}")
print(f"Pass rate: {passed}/{total} = {passed*100//total}%")
print()

failures = [r for r in results if r['status'] == 'FAIL']
if failures:
    print("=== FAILURES ===")
    for r in failures:
        print(f"  {r['name']}: jdiff={r.get('jump_diffs')} tdiff={r.get('true_diffs')}")

with open(os.path.join(TEST_DIR, 'batch_results.json'), 'w', encoding='utf-8') as fp:
    json.dump({'summary': {'total': total, 'passed': passed, 'failed': failed}, 'results': results}, fp, indent=2, ensure_ascii=False)
