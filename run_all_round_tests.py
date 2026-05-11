import os, sys, py_compile, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

def run_round_tests(round_dir):
    results = {'pass': [], 'fail': []}
    
    for f in sorted(os.listdir(round_dir)):
        if not (f.startswith('test_') and f.endswith('.py')):
            continue
        py_path = os.path.join(round_dir, f)
        pyc_path = py_path + 'c'
        
        try:
            py_compile.compile(py_path, pyc_path, doraise=True)
        except Exception as e:
            print(f'COMPILE FAIL: {f}: {e}')
            continue
        
        try:
            module = load_pyc_file_v2(pyc_path)
            if not module or not module.code:
                print(f'LOAD FAIL: {f}')
                results['fail'].append((f, 'load failed'))
                continue
            
            code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
            actual_code = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
            
            cfg = build_cfg(actual_code)
            gen = RegionASTGenerator(cfg)
            ast_dict = gen.generate()
            converter = CFGASTConverter()
            py_ast = converter.convert(ast_dict)
            code_gen = CFGCodeGenerator()
            source = code_gen.generate(py_ast)
            
            if source is None:
                print(f'DECOMPILE FAIL: {f} - source is None')
                results['fail'].append((f, 'source is None'))
                continue
            
            try:
                compile(source, '<decompiled>', 'exec')
            except SyntaxError as e:
                print(f'SYNTAX FAIL: {f} - {e}')
                results['fail'].append((f, f'syntax: {e}'))
                continue
            
            orig_ns = {}
            with open(py_path, 'r', encoding='utf-8') as fh:
                exec(compile(fh.read(), '<original>', 'exec'), orig_ns)
            
            decomp_ns = {}
            exec(compile(source, '<decompiled>', 'exec'), decomp_ns)
            
            orig_funcs = sorted([n for n in orig_ns if callable(orig_ns[n]) and not n.startswith('_')])
            decomp_funcs = sorted([n for n in decomp_ns if callable(decomp_ns[n]) and not n.startswith('_')])
            
            if orig_funcs != decomp_funcs:
                print(f'FUNC MISMATCH: {f} - orig={orig_funcs} decomp={decomp_funcs}')
                results['fail'].append((f, 'func mismatch'))
                continue
            
            sem_ok = True
            sem_err = ''
            for func_name in orig_funcs:
                for args in [(1,), (2,), (3,), (0,), (-1,)]:
                    try:
                        orig_r = orig_ns[func_name](*args)
                    except Exception as e:
                        orig_r = f'EXCEPTION:{type(e).__name__}'
                    try:
                        decomp_r = decomp_ns[func_name](*args)
                    except Exception as e:
                        decomp_r = f'EXCEPTION:{type(e).__name__}'
                    if orig_r != decomp_r:
                        if callable(orig_r) and callable(decomp_r):
                            continue
                        sem_err = f'{func_name}{args}: orig={orig_r} decomp={decomp_r}'
                        sem_ok = False
                        break
                if not sem_ok:
                    break
            
            if sem_ok:
                print(f'PASS: {f}')
                results['pass'].append(f)
            else:
                print(f'SEMANTIC FAIL: {f} - {sem_err}')
                results['fail'].append((f, f'semantic: {sem_err}'))
        
        except Exception as e:
            print(f'ERROR: {f} - {type(e).__name__}: {e}')
            results['fail'].append((f, f'error: {e}'))
        
        if os.path.exists(pyc_path):
            os.remove(pyc_path)
    
    total = len(results['pass']) + len(results['fail'])
    print(f'\n=== SUMMARY ===')
    print(f'PASS: {len(results["pass"])}/{total}')
    print(f'FAIL: {len(results["fail"])}/{total}')
    if results['fail']:
        print(f'\n--- FAILED ---')
        for f, reason in results['fail']:
            print(f'  {f}: {reason[:150]}')
    
    return results

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('round_dir', help='Round directory to test')
    args = parser.parse_args()
    run_round_tests(args.round_dir)
