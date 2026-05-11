import py_compile, sys, os, dis
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')

for tf in ['test_w03_multi_with.py', 'test_w04_nested_with.py', 'test_w06_try_with_with.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    with open(tf) as f:
        code = compile(f.read(), tf, 'exec')
    func_code = code.co_consts[0]
    print(f'=== {tf} BYTECODE ===')
    dis.dis(func_code)
    print(f'\n=== {tf} EXCEPTION TABLE ===')
    for entry in func_code.co_exceptiontable:
        print(f'  start={entry.start}, end={entry.end}, depth={entry.depth}, lasti={entry.lasti}, target={entry.target}')
    print()
    if os.path.exists(pyc):
        os.remove(pyc)
