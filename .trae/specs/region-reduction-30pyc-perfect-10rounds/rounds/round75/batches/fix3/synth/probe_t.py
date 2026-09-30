# -*- coding: utf-8 -*-
import hashlib, io, os, py_compile, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = r'D:\Temp\opencode\r75gate\fix3\synth'
REPO = r'F:\Downloads\pythoncdc-main'
VERIFY = os.path.join(REPO, 'scripts', 'pyc_verify.py')
RUN = r'D:\Temp\opencode\r75gate\fix2\run_arm.py'
SHAPES = {
 't1_or_isnone': '''def t1(a, b):
    if a is None or b is None:
        return None
    return a + b
''',
 't2_or_isnone_try': '''def t2(a, b):
    try:
        if a is None or b is None:
            return None
        return a + b
    except Exception:
        return -1
''',
 't3_or_isnone_nested': '''def t3(x, a, b):
    if x:
        if a is None or b is None:
            return None
        return a + b
    return 0
''',
 't4_or_isnone_chain': '''def t4(k, a, b):
    if k == 1:
        if a is None or b is None:
            return None
        return a + b
    elif k == 2:
        if a is None or b is None:
            return -1
        return a * b
    return 0
''',
 't5_or_isnone_shared_tail': '''def t5(a, b, c):
    r = 0
    if a is None or b is None:
        r = -1
    else:
        r = a + b
    return r + c
''',
}
def sha(t): return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]
def run(arm, pyc, out):
    subprocess.run([sys.executable,'-W','ignore','-X','utf8',RUN,arm,pyc,out],
                   capture_output=True, text=True, timeout=280, errors='replace')
    return os.path.isfile(out)
def ver(pyc, out):
    r = subprocess.run([sys.executable,'-W','ignore','-X','utf8',VERIFY,'single',pyc,'--source',out],
                       capture_output=True, text=True, timeout=280, errors='replace')
    t=[l for l in (r.stdout or '').split('\n') if l.startswith('[single] status')]
    return t[-1] if t else (r.stdout or '')[-120:]
for name, src in SHAPES.items():
    p=os.path.join(HERE,name+'.py')
    io.open(p,'w',encoding='utf-8',newline='\n').write('# -*- coding: utf-8 -*-\n# [R75 fix3 synth]\n'+src)
    py_compile.compile(p, cfile=os.path.join(HERE,name+'.pyc'), doraise=True)
    pyc=os.path.join(HERE,name+'.pyc')
    res={}
    for arm in ('landed','abdef'):
        out=os.path.join(HERE,'out','%s_%s.py'%(arm,name))
        if os.path.exists(out): os.remove(out)
        if run(arm,pyc,out):
            res[arm]=(sha(io.open(out,encoding='utf-8').read()), ver(pyc,out))
        else: res[arm]=('FAIL','')
    hf='failure' in res['landed'][1]; cs='status=success' in res['abdef'][1]
    print('%-24s landed=%s abdef=%s | head_fail=%s cand_ok=%s FLIP=%s' % (
        name, res['landed'][1].replace('[single] status=',''), res['abdef'][1].replace('[single] status=',''),
        hf, cs, hf and cs))
