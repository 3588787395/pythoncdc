import py_compile, sys, os, dis, io

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))

from pycdc import decompile_pyc

checks = ['test_b05_expr_stmt.py', 'test_b08_pass.py', 'test_e01_try_except.py', 'test_w01_with.py']

for tf in checks:
    pyc_path = os.path.join(HERE, tf + 'c')
    test_path = os.path.join(HERE, tf)
    
    py_compile.compile(test_path, cfile=pyc_path, doraise=True)
    src = decompile_pyc(pyc_path)
    
    with open(test_path) as f:
        original_code = compile(f.read(), tf, 'exec')
    decompiled_code = compile(src, '<decomp>', 'exec')
    
    orig_func = original_code.co_consts[0]
    deco_func = decompiled_code.co_consts[0]
    
    is_match = orig_func.co_code == deco_func.co_code
    print(f"\n{'='*60}")
    print(f"{tf}: MATCH={is_match}")
    if not is_match:
        print(f"  ORIG: {list(orig_func.co_code)}")
        print(f"  DECO: {list(deco_func.co_code)}")
        print(f"  ORIG len={len(orig_func.co_code)}, DECO len={len(deco_func.co_code)}")
        print(f"  DECOMPILED SOURCE:\n{src}")
    
    os.remove(pyc_path)
