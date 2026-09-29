# -*- coding: utf-8 -*-
"""fix1 synth: 最小复现 + 负例 for sub-mechanism "块尾条件跳转的 fall-through 是区域 entry 时，
前导条件操作数被 _cjb_skip_inline_if 丢弃"（jq_trans_module 63/65 -> 65/65 的根因）。

产物（全部在工作区，不写 repo）：
  synth/repro75_jqcond.py|.pyc     最小复现：真实失败单元 func_get_bars_convert_code 的单函数切片
  synth/neg75_jqcond.py|.pyc       负例：同族布尔条件但不触发丢弃路径
  synth/out/<arm>_<name>.py        head / jqop1 两臂反编译产物
  synth/out/<name>.json            sha16 + mandated 判据读数

断言：
  repro: head 产物 != cand 产物；head mandated=failure，cand mandated=success
  neg:   head sha == cand sha（负例逐字节相同）
"""
import hashlib
import importlib.util as iu
import io
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = r'D:/Temp/opencode/r75gate/center'
REPO = r'F:\Downloads\pythoncdc-main'
OKPY = r'D:/Temp/opencode/r75gate/fix1/jq_jqop1.py'
VERIFY = os.path.join(REPO, 'scripts', 'pyc_verify.py')
sys.stdout.reconfigure(encoding='utf-8')

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)


def slice_func(path, name):
    L = io.open(path, encoding='utf-8').read().split('\n')
    s = None
    for i, l in enumerate(L):
        if l.startswith('def %s(' % name):
            s = i
            break
    assert s is not None, name
    e = s + 1
    while e < len(L) and (L[e].startswith((' ', '\t')) or L[e].strip() == ''):
        e += 1
    body = L[s:e]
    while body and body[-1].strip() == '':
        body.pop()
    return '\n'.join(body) + '\n'


repro_src = ('# -*- coding: utf-8 -*-\n'
             '# [R75 fix1 synth] 最小复现：jq_trans_module 的失败单元单函数切片。\n'
             'import re\n\n'
             + slice_func(OKPY, 'func_get_bars_convert_code'))

neg_src = ('# -*- coding: utf-8 -*-\n'
           '# [R75 fix1 synth] 负例：同族布尔条件（and / or 链），但不落在\n'
           '# 「块尾条件跳转 fall-through = 区域 entry」的丢弃路径上，\n'
           '# 两臂产物 sha 必须与落地逐字节相同，且 mandated 判据两侧均 success。\n'
           'def neg_a(s, flag):\n'
           '    if flag:\n'
           '        return 0\n'
           "    if '(' in s and ')' not in s:\n"
           '        return 1\n'
           "    if '[' in s or ']' not in s:\n"
           '        return 2\n'
           '    return 3\n'
           '\n'
           'def neg_c(s):\n'
           '    hit = 0\n'
           "    if '(' in s:\n"
           '        hit += 1\n'
           "    elif 'x' in s and 'y' in s:\n"
           '        hit += 2\n'
           "    if '(' in s and ')' not in s or '[' in s and ']' not in s:\n"
           '        hit += 4\n'
           '    return hit\n')

for nm, txt in (('repro75_jqcond', repro_src), ('neg75_jqcond', neg_src)):
    io.open(os.path.join(HERE, nm + '.py'), 'w', encoding='utf-8', newline='\n').write(txt)
    py_compile.compile(os.path.join(HERE, nm + '.py'),
                       cfile=os.path.join(HERE, nm + '.pyc'), doraise=True)
    print('built %s.py / %s.pyc (%d lines)' % (nm, nm, txt.count('\n')))


def load_arm(arm):
    return os.path.join(os.path.dirname(HERE), 'run_arm.py')


def sha(t):
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]


rows = {}
for name in ('repro75_jqcond', 'neg75_jqcond'):
    pyc = os.path.join(HERE, name + '.pyc')
    got = {}
    for arm in ('head', 'jqop1'):
        out = os.path.join(HERE, 'out', '%s_%s.py' % (arm, name))
        r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8',
                            os.path.dirname(HERE) + '/run_arm.py', arm, pyc, out],
                           capture_output=True, text=True, timeout=280, errors='replace')
        assert os.path.isfile(out), '%s %s %s' % (arm, name, (r.stdout or '')[-400:])
        text = io.open(out, encoding='utf-8').read()
        r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', VERIFY, 'single',
                            pyc, '--source', out], capture_output=True, text=True,
                           timeout=280, errors='replace')
        tail = [l for l in (r.stdout or '').split('\n') if l.startswith('[single] status')]
        got[arm] = {'sha': sha(text), 'out': out,
                    'verify': tail[-1].strip() if tail else (r.stdout or '')[-200:]}
        print('%-16s %-6s sha=%s  %s' % (name, arm, got[arm]['sha'], got[arm]['verify']))
    rows[name] = got

rep, neg = rows['repro75_jqcond'], rows['neg75_jqcond']
verdict = {
    'repro_shas_differ': rep['head']['sha'] != rep['jqop1']['sha'],
    'repro_head_failure': 'failure' in rep['head']['verify'],
    'repro_cand_success': 'status=success' in rep['jqop1']['verify'],
    'neg_sha_identical': neg['head']['sha'] == neg['jqop1']['sha'],
}
print(json.dumps(verdict, indent=1))
ok = all(verdict.values())
io.open(os.path.join(HERE, 'out', 'synth.json'), 'w', encoding='utf-8',
        newline='\n').write(json.dumps({'verdict': verdict, 'rows': rows}, ensure_ascii=False,
                                       indent=1))
print('SYNTH %s' % ('PASS' if ok else 'FAIL'))
