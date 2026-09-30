# -*- coding: utf-8 -*-
"""fix3 G0 / 硬规则自检（BRIEF_fix3 §G0）。

读 specs/{or1,sink1,chf1,e1,f1}.json（合并 = tmp/abdef.json，5 edits，均落在
core/cfg/region_analyzer.py）+ 反打后的完整文件，逐条给可复现读数：
  1. 三要素注释：spec 级 repl 合并文本含「根因 / 同层身份判据 / 去向与守卫」
  2. 禁止项（只看**代码行**，剥掉注释与字符串字面量）：
     新增 self 状态（赋值 / getattr(self,..) / setattr(self,..)）、
     跨层 `X.entry in Y.blocks`、函数名/文件名白名单、偏移阈值、名字白名单
  3. 文件语法：ast.parse + py_compile，BOM 与原件一致
  4. repo 的 core/ scripts/ site-packages/ 无任何已跟踪改动（不改 repo、不手改 *OK.py）
"""
import ast
import io
import json
import os
import py_compile
import re
import subprocess
import sys
import tempfile

REPO = r'F:\Downloads\pythoncdc-main'
GATE = r'D:/Temp/opencode/r75gate'
HERE = os.path.dirname(os.path.abspath(__file__))
PAIRS = ((os.path.join(GATE, 'fix3', 'tmp', 'abdef.json'), 'core/cfg/region_analyzer.py'),)
MIRR = os.path.join(GATE, 'center', 'mirr_abdef')
sys.stdout.reconfigure(encoding='utf-8')

checks = []


def chk(name, ok, detail=''):
    checks.append((name, bool(ok), detail))


# ---- 1. 三要素（spec 级） ----
keys = ('根因', '同层身份判据', '去向与守卫')
full = []
for spec_path, _rel in PAIRS:
    spec = json.load(io.open(spec_path, encoding='utf-8'))
    full.append(' '.join(e.get('repl', '') for e in spec['edits']))
full = ' '.join(full)
chk('spec 三要素注释(根因/同层身份判据/去向与守卫)',
    all(k in full for k in keys),
    str([k for k in keys if k not in full]) or 'all present')

# ---- 2. 逐文件：反打 + 新增行 code-only 禁止项 ----
from collections import Counter
for spec_path, rel in PAIRS:
    spec = json.load(io.open(spec_path, encoding='utf-8'))
    core = os.path.join(REPO, rel)
    src = io.open(core, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
    patched = src
    for k, e in enumerate(spec['edits']):
        assert patched.count(e['anchor']) == 1, '%s anchor %d count=%d' % (
            rel, k, patched.count(e['anchor']))
        patched = patched.replace(e['anchor'], e['repl'])

    added = []
    for e in spec['edits']:
        d = Counter(e['repl'].split('\n')) - Counter(e['anchor'].split('\n'))
        for ln, n in d.items():
            added.extend([ln] * n)

    code_lines = []
    in_doc = False
    for ln in added:
        s = ln
        if '"""' in s:
            if in_doc:
                in_doc = False
                continue
            head = s.split('"""')[0]
            if head.strip():
                code_lines.append(head.split('#')[0])
            if s.count('"""') == 1:
                in_doc = True
            continue
        if in_doc:
            continue
        s = s.split('#')[0]
        if s.strip():
            code_lines.append(s)
    code = '\n'.join(code_lines)
    tag = os.path.basename(rel)

    chk('[%s] 新增代码无 self 状态赋值' % tag,
        not re.search(r'\bself\.\w+\s*=[^=]', code),
        re.findall(r'\bself\.\w+\s*=[^=]', code) or 'none')
    chk('[%s] 新增代码无 getattr/setattr(self,...)' % tag,
        not re.search(r'(?:get|set)attr\(\s*self\b', code),
        re.findall(r'(?:get|set)attr\(\s*self\b', code) or 'none')
    chk('[%s] 新增代码无跨层 X.entry in Y.blocks' % tag,
        not re.search(r'\w+\.entry\s+in\s+\w+\.blocks', code),
        re.findall(r'\w+\.entry\s+in\s+\w+\.blocks', code) or 'none')
    chk('[%s] 新增代码无文件名字面量 (.py/路径)' % tag,
        not re.search(r"['\"][\w./\\-]+\.py['\"]", code),
        re.findall(r"['\"][\w./\\-]+\.py['\"]", code) or 'none')
    names = ('filter_desicion', 'next_day', 'get_price', 'get_kline_by_count',
             'can_cancel_order', 'memory_handler', 'run_tick_socket', 'get_fields',
             'get_real_minute_kline', 'get_tick_direction')
    hit = [n for n in names if n in code]
    chk('[%s] 新增代码无靶单元函数名/文件名白名单' % tag, not hit, hit or 'none')
    chk('[%s] 新增代码无 start_offset 偏移阈值' % tag,
        not re.search(r'start_offset\s*[<>]=?\s*\d|start_offset\s*==\s*\d+', code),
        re.findall(r'start_offset\s*[<>]=?\s*\d+|start_offset\s*==\s*\d+', code) or 'none')

    try:
        ast.parse(patched)
        ok, d = True, 'ast.parse OK'
    except Exception as exc:
        ok, d = False, repr(exc)
    chk('[%s] 反打文件 ast.parse' % tag, ok, d)
    try:
        tf = os.path.join(tempfile.gettempdir(), 'fix3_g0_%s' % tag)
        io.open(tf, 'w', encoding='utf-8', newline='\n').write(patched)
        py_compile.compile(tf, cfile=tf + 'c', doraise=True)
        ok, d = True, 'py_compile OK'
    except Exception as exc:
        ok, d = False, repr(exc)
    chk('[%s] 反打文件 py_compile' % tag, ok, d)

    orig_bom = io.open(core, 'rb').read(3) == b'\xef\xbb\xbf'
    new_bom = io.open(os.path.join(MIRR, rel.replace('/', os.sep)), 'rb').read(3) == b'\xef\xbb\xbf'
    chk('[%s] BOM 与原件一致' % tag, orig_bom == new_bom, 'orig=%s new=%s' % (orig_bom, new_bom))

# ---- 4. repo 未被写入 ----
r = subprocess.run(['git', '-C', REPO, 'status', '--porcelain', '--', 'core', 'scripts',
                    'site-packages'], capture_output=True, text=True, errors='replace')
dirty = [l for l in (r.stdout or '').split('\n') if l.strip()]
tracked = [l for l in dirty if not l.startswith('??')]
chk('repo core/scripts/site-packages 已跟踪文件零改动（不改 repo、不手改 *OK.py）',
    not tracked, tracked[:5] or 'clean (untracked=%d)' % len([l for l in dirty if l.startswith('??')]))

print('%-70s %-5s %s' % ('check', 'ok', 'detail'))
for n, ok, d in checks:
    print('%-70s %-5s %s' % (n, 'PASS' if ok else 'FAIL', str(d)[:110]))
allok = all(c[1] for c in checks)
summary = 'G0-audit: %s (%d/%d)' % ('PASS' if allok else 'FAIL',
                                    sum(c[1] for c in checks), len(checks))
print(summary)
io.open(os.path.join(GATE, 'fix3', 'dump', 'g0audit.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join('%s\t%s\t%s' % (n, 'PASS' if ok else 'FAIL', d) for n, ok, d in checks)
    + '\n%s\n' % summary)
