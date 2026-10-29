import sys, py_compile, subprocess, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')

cases = {
 'simple': "c=True\nA=1\nB=2\nX = (A if c else B)\n",
 'and_chain': "a=True\nb=True\nA=1\nB=2\nX = (A if (a and b) else B)\n",
 'or_chain': "a=True\nb=True\nA=1\nB=2\nX = (A if (a or b) else B)\n",
 'or_of_and': "a=True\nb=True\nc=True\nd=True\nA=1\nB=2\nX = (A if (a and b) or (c and d) else B)\n",
 'or_three': "a=True\nb=True\ncc=True\nA=1\nB=2\nX = (A if a or b or cc else B)\n",
}

os.chdir(r'D:\temp\opencode')
for name, src in cases.items():
    open(f'tc_{name}.py','w',encoding='utf-8').write(src)
    py_compile.compile(f'tc_{name}.py', cfile=f'tc_{name}.pyc', doraise=True)
    r = subprocess.run([sys.executable, '-X','utf8', r'F:\Downloads\pythoncdc-main\pycdc.py', f'tc_{name}.pyc', '-o', f'tc_{name}_out.py'], capture_output=True, text=True)
    out = open(f'tc_{name}_out.py', encoding='utf-8').read()
    # get the X= lines
    body = [l for l in out.split(chr(10)) if 'X' in l or 'if ' in l or 'else' in l or l.strip() in ('A','B','1','2')]
    ok = ('X = (A if' in out) or ('X = A if' in out) or ('X = (1 if' in out) or ('X = 1 if' in out)
    print(f'--- {name}: ternary_preserved={ok}')
    for l in out.split(chr(10)):
        if l.strip() and not l.startswith('#'):
            print('   ', l)
