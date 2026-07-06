import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc
from dis import get_instructions

def norm(code_obj):
    return tuple(i.opname for i in get_instructions(code_obj) if not i.opname.startswith('CACHE'))

test_files = [
    'test_e01_try_except.py',
    'test_e02_multi_except.py',
    'test_e03_try_else_finally.py',
    'test_e04_try_finally.py',
    'test_e05_try_except_finally.py',
    'test_e06_full_combination.py',
    'test_e07_except_as.py',
    'test_e08_bare_except.py',
    'test_e09_nested_try.py',
]

for tf in test_files:
    if not os.path.exists(tf):
        print("%s: SKIP (not found)" % tf)
        continue
    pyc = tf + 'c'
    try:
        py_compile.compile(tf, cfile=pyc, doraise=True)
        src = decompile_pyc(pyc)
        with open(tf) as f:
            oc = compile(f.read(), tf, 'exec')
        dc = compile(src, '<d>', 'exec')

        all_match = True
        for idx in range(len(oc.co_consts)):
            cc = oc.co_consts[idx]
            if hasattr(cc, 'co_code'):
                dcc = dc.co_consts[idx] if idx < len(dc.co_consts) else None
                if dcc is None or not hasattr(dcc, 'co_code'):
                    all_match = False
                    break
                on = norm(cc)
                dn = norm(dcc)
                if on != dn:
                    all_match = False
                    break

        match = "MATCH" if all_match else "DIFF"
        print("%s: %s" % (tf, match))
        if not all_match:
            print("  Decompiled source:")
            for line in src.split('\n')[:20]:
                print("  ", line)
    except Exception as e:
        print("%s: ERROR %s" % (tf, str(e)))
    finally:
        if os.path.exists(pyc):
            os.remove(pyc)
