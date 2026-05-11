import sys, os, py_compile, io
os.chdir(r'd:\Desktop\ptrade相关\pythoncdc\testqouter\round1')
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

from pycdc import PycDecompiler

for tf in ['test_w01_with.py', 'test_w02_with_no_as.py']:
    pyc = tf + 'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    
    decompiler = PycDecompiler()
    decompiler.load_file(pyc)
    
    output = io.StringIO()
    decompiler.decompile(output, use_region=True)
    src = output.getvalue()
    
    lines = src.split('\n')
    clean = [l for l in lines if not l.startswith('#') or l.startswith('# Decompiled')]
    
    with open(f'_out_{tf}', 'w', encoding='utf-8') as f:
        f.write(f'=== {tf} ===\n')
        for i, line in enumerate(clean):
            f.write(f'{i:3d}: {line}\n')
        f.write('\n')
    
    if os.path.exists(pyc):
        os.remove(pyc)

print('Done. Output written to _out_*.txt files.')
