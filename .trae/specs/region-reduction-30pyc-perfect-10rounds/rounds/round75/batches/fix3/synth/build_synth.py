# -*- coding: utf-8 -*-
"""fix3 synth: 复现 + 真嵌套负例（BRIEF_fix3 §3 synth 项）。

  repro75_f3_orchain.pyc   复现 = t2：or-is-None 链落在 try 体内、try 尾有共享
                           except/续行（「try 内共享尾」最小复现）。
                           head(landed) failure 1/2 -> arm(abdef) success 2/2
                           （landed 的链守卫拒绝 IF_NONE 首段，链退化成
                           `if not A:` 反转 + 嵌套 if，控制流多一层即 pbv 失败）
  neg75_f3_nested.py|.pyc  负例 = 真嵌套 try（try 内再 try，两层 handler），
                           两臂产物 sha16 必须逐字节相同。

产物（全部在工作区，不写 repo）：
  synth/out/<arm>_<name>.py   landed / abdef 两臂反编译产物
  synth/out/synth.json        sha16 + verify 读数 + verdict

断言：
  repro: head 产物 != cand 产物；head mandated=failure，cand mandated=success
  neg:   head sha == cand sha（负例逐字节相同）
"""
import hashlib
import io
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r'F:\Downloads\pythoncdc-main'
VERIFY = os.path.join(REPO, 'scripts', 'pyc_verify.py')
RUN = r'D:\Temp\opencode\r75gate\fix2\run_arm.py'
sys.stdout.reconfigure(encoding='utf-8')
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)

REPRO_SRC = '''def t2(a, b):
    try:
        if a is None or b is None:
            return None
        return a + b
    except Exception:
        return -1
'''

NEG_SRC = '''def neg_nested_try(x):
    try:
        try:
            return 10 / x
        except ZeroDivisionError:
            return -1
    except Exception:
        return -2


def neg_nested_try_loop(n):
    total = 0
    try:
        try:
            for i in range(n):
                total += i
        except ValueError:
            total = 0
        return total
    except RuntimeError:
        return -3
'''

for name, txt in (('repro75_f3_orchain', REPRO_SRC), ('neg75_f3_nested', NEG_SRC)):
    p = os.path.join(HERE, name + '.py')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(
        '# -*- coding: utf-8 -*-\n'
        '# [R75 fix3 synth] %s\n' % ('复现：try 内共享尾 + or-is-None 链'
                                     if name.startswith('repro') else
                                     '负例：真嵌套 try（两层 handler），两臂必须逐字节相同')
        + txt)
    py_compile.compile(p, cfile=os.path.join(HERE, name + '.pyc'), doraise=True)
    print('built %s.py / %s.pyc' % (name, name))


def sha(t):
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]


def decompile(arm, pyc, out):
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', RUN, arm, pyc, out],
                       capture_output=True, text=True, timeout=280, errors='replace')
    return os.path.isfile(out)


def verify(pyc, out):
    r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', VERIFY, 'single', pyc,
                        '--source', out], capture_output=True, text=True, timeout=280,
                       errors='replace')
    tail = [l for l in (r.stdout or '').split('\n') if l.startswith('[single] status')]
    return tail[-1].strip() if tail else (r.stdout or '')[-160:]


rows = {}
for name in ('repro75_f3_orchain', 'neg75_f3_nested'):
    pyc = os.path.join(HERE, name + '.pyc')
    got = {}
    for arm in ('landed', 'abdef'):
        out = os.path.join(HERE, 'out', '%s_%s.py' % (arm, name))
        if os.path.exists(out):
            os.remove(out)
        assert decompile(arm, pyc, out), '%s %s decompile failed' % (arm, name)
        text = io.open(out, encoding='utf-8').read()
        got[arm] = {'sha': sha(text), 'out': out, 'verify': verify(pyc, out)}
        print('%-22s %-8s sha=%s  %s' % (name, arm, got[arm]['sha'], got[arm]['verify']))
    rows[name] = got

rep, neg = rows['repro75_f3_orchain'], rows['neg75_f3_nested']
verdict = {
    'repro_shas_differ': rep['landed']['sha'] != rep['abdef']['sha'],
    'repro_head_failure': 'failure' in rep['landed']['verify'],
    'repro_cand_success': 'status=success' in rep['abdef']['verify'],
    'neg_sha_identical': neg['landed']['sha'] == neg['abdef']['sha'],
    'neg_both_success': ('status=success' in neg['landed']['verify']
                         and 'status=success' in neg['abdef']['verify']),
}
print(json.dumps(verdict, indent=1))
ok = all(verdict.values())
io.open(os.path.join(HERE, 'out', 'synth.json'), 'w', encoding='utf-8', newline='\n').write(
    json.dumps({'verdict': verdict, 'rows': rows}, ensure_ascii=False, indent=1))
print('SYNTH %s' % ('PASS' if ok else 'FAIL'))
sys.exit(0 if ok else 1)
