#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""9.2 位0：B124 四臂只读归属（ana_ab3_r137 同款方法：字节备份→改臂→regen+verify→还原→哈希证明）。

单臂单调用（300s 纪律）：python -X utf8 r9v9fix_b124_4arm.py <arm>
  arm ∈ control | off_b104r3 | off_b99 | off_h3 | off_b104r3_b99 | off_b104r3_h3
        | off_b99_h3 | off_all3 | off_b117 | off_r2186
  off_b117   = 关 [B117] 挂起循环回边块不认领守卫（generator H4 串联守卫之 v2 半）
  off_r2186  = 关 [R21-86] released else 块不认领守卫（generator H4 串联守卫之 v3 半）
证据（增量合并）：r9v9fix_b124_4arm.json；每臂结束还原核心字节并校验 sha256。
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
ANA = os.path.join(ROOT, 'core', 'cfg', 'region_analyzer.py')
GEN = os.path.join(ROOT, 'core', 'cfg', 'region_ast_generator.py')
BAKDIR = r'D:\Temp\opencode\r92bak'
OUT = os.path.join(HERE, 'r9v9fix_b124_4arm.json')

PROBES = [
    ('e05', 'test_repros/round3/e05_g3_compare_chain.pyc'),
    ('e10', 'test_repros/round3/e10_g7_call_args.pyc'),
    ('r8_10', 'test_repros/round8/r8_10_expr_cross_stmt.pyc'),
]
B124_UNITS = {
    'e05': ['f_compare_chain6', 'f_compare_binop_inside', 'f_compare_subscript_inside'],
    'e10': ['f_call_ternary_arg'],
    'r8_10': ['r8_x_with_ternary'],
}

_A_R3 = ("            if block in released:\r\n",
         "            if False and (block in released):\r\n")
_A_B99 = ("                if _b99_block_in_value_boolop:\r\n",
          "                if False and _b99_block_in_value_boolop:\r\n")
_G_H3 = ("            if _r2115_tail_blocks or _r62_hoist_blocks:\r\n",
         "            _r2115_tail_blocks = []\r\n            _r62_hoist_blocks = []\r\n"
         "            if _r2115_tail_blocks or _r62_hoist_blocks:\r\n")

EDITS = {
    'control': [],
    'off_b104r3': [(ANA,) + _A_R3],
    'off_b99': [(ANA,) + _A_B99],
    'off_h3': [(GEN,) + _G_H3],
    'off_b104r3_b99': [(ANA,) + _A_R3, (ANA,) + _A_B99],
    'off_b104r3_h3': [(ANA,) + _A_R3, (GEN,) + _G_H3],
    'off_b99_h3': [(ANA,) + _A_B99, (GEN,) + _G_H3],
    'off_all3': [(ANA,) + _A_R3, (ANA,) + _A_B99, (GEN,) + _G_H3],
}

STAT_RE = re.compile(r'status=(\w+)\s+units=(\d+)/(\d+)')
FAIL_RE = re.compile(r'^\s*\*\*\*.*?:\s*Failure.*$')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def read_text(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def write_text(path, text):
    with open(path, 'wb') as f:
        f.write(text.encode('utf-8'))


def apply_edits(arm):
    for path, old, new in EDITS[arm]:
        text = read_text(path)
        n = text.count(old)
        assert n == 1, 'anchor not unique (%d) in %s: %r' % (n, path, old)
        write_text(path, text.replace(old, new))


def restore_all():
    for name in ('region_analyzer.py', 'region_ast_generator.py'):
        with open(os.path.join(BAKDIR, name), 'rb') as f:
            data = f.read()
        with open(os.path.join(ROOT, 'core', 'cfg', name), 'wb') as f:
            f.write(data)


def run(cmd, timeout=200):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (p.stdout or '') + (p.stderr or '')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'


def probe(rel):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok = full[:-4] + 'OK.py'
    run([sys.executable, os.path.join(ROOT, 'pycdc.py'), full, '-o', ok])
    out = run([sys.executable, os.path.join(ROOT, 'scripts', 'pyc_verify.py'),
               'single', full])
    status, us, ut = None, None, None
    for line in out.splitlines():
        m = STAT_RE.search(line)
        if m:
            status, us, ut = m.group(1), int(m.group(2)), int(m.group(3))
    fails = [l.strip() for l in out.splitlines() if FAIL_RE.match(l)]
    return {'pyc': rel, 'status': status, 'units_success': us,
            'units_total': ut, 'failures': fails}


def load_results():
    if os.path.exists(OUT):
        try:
            with open(OUT, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'shas': {}, 'results': {}}


def main():
    arm = sys.argv[1]
    assert arm in EDITS, 'unknown arm %s' % arm
    os.makedirs(BAKDIR, exist_ok=True)
    for name in ('region_analyzer.py', 'region_ast_generator.py'):
        src = os.path.join(ROOT, 'core', 'cfg', name)
        dst = os.path.join(BAKDIR, name)
        if not os.path.exists(dst):
            with open(src, 'rb') as f, open(dst, 'wb') as g:
                g.write(f.read())
    base_shas = {name: sha(os.path.join(BAKDIR, name))
                 for name in ('region_analyzer.py', 'region_ast_generator.py')}
    res = load_results()
    res['shas'] = base_shas
    try:
        apply_edits(arm)
        row = {}
        for name, rel in PROBES:
            r = probe(rel)
            b124_fail = [u for u in B124_UNITS[name]
                         if any(('.' + u + ':') in fl for fl in r['failures'])]
            row[name] = {'reading': '%s %s/%s' % (r['status'], r['units_success'],
                                                  r['units_total']),
                         'b124_fail': b124_fail, 'failures': r['failures']}
            print('[%-14s %-6s] %-8s %s/%s  B124fail=%s' % (
                arm, name, r['status'], r['units_success'], r['units_total'],
                b124_fail), flush=True)
        res['results'][arm] = row
    finally:
        restore_all()
        for name, s in base_shas.items():
            cur = sha(os.path.join(ROOT, 'core', 'cfg', name))
            assert cur == s, 'RESTORE FAILED %s: %s != %s' % (name, cur, s)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print('-> %s (arms done: %s)' % (os.path.basename(OUT),
                                     sorted(res['results'])))


if __name__ == '__main__':
    main()
