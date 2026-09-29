# -*- coding: utf-8 -*-
"""fix2 synth: 复现 + 负例 for this batch's two rules.

  repro75_tiu.pyc             复现 = 真身 IQCommon/util/trade_info_utils.pyc
                              head failure 36/41 -> arm success 41/41
                              （切片不触发：几何差 4 字节，probe_repro.py 5 形状 + 
                               slice75_trytail 读数入档）
  neg75_trytail.py|.pyc       负例：同族结构但两臂都必须逐字节相同 ——
                              (a) break 目标在 try 体内（属 region.blocks）；
                              (b) 分支尾块含用户语句后再隐式 return（edit-D2 纯度判据
                              必须拒绝剔除，否则语句外提，见 asset_storage::load 回归）。

产物（全部在工作区，不写 repo）：
  synth/out/<arm>_<name>.py   landed / ec_afgd5b 两臂反编译产物
  synth/out/synth.json        sha16 + mandated 判据读数

断言：
  repro: head 产物 != cand 产物；head mandated=failure，cand mandated=success
  neg:   head sha == cand sha（负例逐字节相同）
"""
import ast
import hashlib
import io
import json
import os
import py_compile
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = r'F:\Downloads\pythoncdc-main'
OKPY = os.path.join(REPO, 'site-packages', 'IQCommon', 'util', 'trade_info_utilsOK.py')
VERIFY = os.path.join(REPO, 'scripts', 'pyc_verify.py')
sys.stdout.reconfigure(encoding='utf-8')

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)


def slice_func(path, name):
    src = io.open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            seg = ast.get_source_segment(src, node)
            assert seg, name
            return seg + '\n'
    raise AssertionError('not found: %s' % name)


def module_header(path):
    """imports / module prologue: names must stay *bound* so that CPython emits the
    same `LOAD_GLOBAL NULL+x; LOAD_ATTR` form as the real pyc (unbound globals take
    the LOAD_METHOD path, which changes bytecode geometry and hides the defect)."""
    src = io.open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    cut = len(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            cut = _line_off(src, node.lineno)
            break
    return src[:cut].rstrip('\n') + '\n'


def _line_off(src, lineno):
    off = 0
    for _ in range(lineno - 1):
        n = src.find('\n', off)
        assert n != -1
        off = n + 1
    return off


slice_src = ('# -*- coding: utf-8 -*-\n'
             '# [R75 fix2 synth] 三函数切片（不入判据）：jump 目标几何与真身相差 4 字节\n'
             '# （LOAD_GLOBAL NULL 位 / 目标行表），两臂产物不同但 mandated 均 success，\n'
             '# 说明最小复现必须保留真身字节码几何 => repro 用真身 pyc。\n'
             + module_header(OKPY) + '\n'
             + slice_func(OKPY, 'kill_trade_process')
             + '\n' + slice_func(OKPY, 'query_strategy_id')
             + '\n' + slice_func(OKPY, 'query_trade_strategy_info'))

neg_src = ('# -*- coding: utf-8 -*-\n'
           '# [R75 fix2 synth] 负例：与 repro 同族但两臂必须逐字节相同。\n'
           '#   neg_try_for  break 目标在 try 体内（属 region.blocks）\n'
           '#   neg_pure_tail 分支尾块含用户语句后再隐式 return None\n'
           '#                （edit-D2 纯度判据必须拒绝剔除，否则语句外提）\n'
           'import os\n\n\n'
           'def neg_try_for(n):\n'
           '    total = 0\n'
           '    try:\n'
           '        for i in range(n):\n'
           '            if i % 7 == 0:\n'
           '                break\n'
           '            total += i\n'
           '        return total\n'
           '    except BaseException:\n'
           '        return -1\n'
           '\n\n'
           'def neg_pure_tail(new_assets, cond, log):\n'
           '    if cond:\n'
           '        return 1\n'
           '    else:\n'
           '        new_assets = list(new_assets)\n'
           '        for item in new_assets:\n'
           '            if item:\n'
           '                break\n'
           '        del new_assets\n'
           '        log.append("done")\n'
           '    return 0\n')

for nm, txt in (('slice75_trytail', slice_src), ('neg75_trytail', neg_src)):
    io.open(os.path.join(HERE, nm + '.py'), 'w', encoding='utf-8', newline='\n').write(txt)
    py_compile.compile(os.path.join(HERE, nm + '.py'),
                       cfile=os.path.join(HERE, nm + '.pyc'), doraise=True)
    print('built %s.py / %s.pyc (%d lines)' % (nm, nm, txt.count('\n')))

REAL = os.path.join(REPO, 'site-packages', 'IQCommon', 'util', 'trade_info_utils.pyc')
io.open(os.path.join(HERE, 'repro75_tiu.pyc'), 'wb').write(io.open(REAL, 'rb').read())
io.open(os.path.join(HERE, 'repro75_tiu.note'), 'w', encoding='utf-8', newline='\n').write(
    'repro = 真身 IQCommon/util/trade_info_utils.pyc（36/41 failure -> 41/41 success）\n'
    'source = site-packages/IQCommon/util/trade_info_utilsOK.py\n'
    '切片尝试不触发：synth/probe_repro.py 5 个合成形状两臂均同，\n'
    'slice75_trytail 两臂 sha 不同但 mandated 均 success（几何差 4 字节）。\n')
print('copied real pyc repro75_tiu.pyc (%d bytes)' % os.path.getsize(os.path.join(HERE, 'repro75_tiu.pyc')))


def sha(t):
    return hashlib.sha256(t.encode('utf-8')).hexdigest()[:16]


rows = {}
for name in ('repro75_tiu', 'neg75_trytail'):
    pyc = os.path.join(HERE, name + '.pyc')
    got = {}
    for arm in ('landed', 'ec_afgd5b'):
        out = os.path.join(HERE, 'out', '%s_%s.py' % (arm, name))
        r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8',
                            os.path.join(HERE, '..', 'run_arm.py'), arm, pyc, out],
                           capture_output=True, text=True, timeout=280, errors='replace')
        assert os.path.isfile(out), '%s %s %s' % (arm, name, (r.stdout or '')[-400:])
        text = io.open(out, encoding='utf-8').read()
        r = subprocess.run([sys.executable, '-W', 'ignore', '-X', 'utf8', VERIFY, 'single',
                            pyc, '--source', out], capture_output=True, text=True,
                           timeout=280, errors='replace')
        tail = [l for l in (r.stdout or '').split('\n') if l.startswith('[single] status')]
        got[arm] = {'sha': sha(text), 'out': out,
                    'verify': tail[-1].strip() if tail else (r.stdout or '')[-200:]}
        print('%-18s %-10s sha=%s  %s' % (name, arm, got[arm]['sha'], got[arm]['verify']))
    rows[name] = got

rep, neg = rows['repro75_tiu'], rows['neg75_trytail']
verdict = {
    'repro_shas_differ': rep['landed']['sha'] != rep['ec_afgd5b']['sha'],
    'repro_head_failure': 'failure' in rep['landed']['verify'],
    'repro_cand_success': 'status=success' in rep['ec_afgd5b']['verify'],
    'neg_sha_identical': neg['landed']['sha'] == neg['ec_afgd5b']['sha'],
}
print(json.dumps(verdict, indent=1))
ok = all(verdict.values())
io.open(os.path.join(HERE, 'out', 'synth.json'), 'w', encoding='utf-8',
        newline='\n').write(json.dumps({'verdict': verdict, 'rows': rows},
                                       ensure_ascii=False, indent=1))
print('SYNTH %s' % ('PASS' if ok else 'FAIL'))
