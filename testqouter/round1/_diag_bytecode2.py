import py_compile, sys, os, dis
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')

for tf in ['test_w04_nested_with.py']:
    with open(tf) as f:
        code = compile(f.read(), tf, 'exec')
    func_code = code.co_consts[0]
    print(f'=== {tf} BYTECODE ===')
    dis.dis(func_code)
    print()
