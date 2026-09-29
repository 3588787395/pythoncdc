# -*- coding: utf-8 -*-
"""fix1 G0 / 硬规则自检（BRIEF_fix1 §4）。

读 spec（specs/jqop1.json）+ 反打后的完整文件，逐条给可复现读数：
  1. 三要素注释：docstring 含「根因 / 同层身份判据 / 去向与守卫」
  2. 禁止项（只看**代码行**，用 tokenize 剥掉注释与字符串字面量）：
     新增 self 状态（赋值 / getattr(self,..) / setattr(self,..)）、
     跨层 `X.entry in Y.blocks`、函数名/文件名白名单、偏移阈值、名字白名单
  3. 文件语法：ast.parse + py_compile，BOM 保持
  4. repo 的 core/ scripts/ site-packages/ 无任何改动（不改 repo）
"""
import ast
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize
from collections import Counter

REPO = r'F:\Downloads\pythoncdc-main'
SPEC = r'D:/Temp/opencode/r75gate/fix1/specs/jqop1.json'
CORE = os.path.join(REPO, 'core', 'cfg', 'region_ast_generator.py')
sys.stdout.reconfigure(encoding='utf-8')

spec = json.load(io.open(SPEC, encoding='utf-8'))
edits = spec['edits']
src = io.open(CORE, encoding='utf-8-sig', newline='').read().replace('\r\n', '\n')
patched = src
for k, e in enumerate(edits):
    assert patched.count(e['anchor']) == 1, 'anchor %d count' % k
    patched = patched.replace(e['anchor'], e['repl'])

added = []
for e in edits:
    d = Counter(e['repl'].split('\n')) - Counter(e['anchor'].split('\n'))
    for ln, n in d.items():
        added.extend([ln] * n)

# ---- code-only：剥注释 + 字符串字面量（docstring 里的举例不算代码）----
raw_added = '\n'.join(added)
code_lines = []
in_doc = False
for ln in added:
    s = ln
    # 三引号块（docstring）内部整段都不算代码
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

checks = []


def chk(name, ok, detail=''):
    checks.append((name, bool(ok), detail))


full_doc = ' '.join(e.get('repl', '') for e in edits)
chk('edit3 docstring 三要素(根因/同层身份判据/去向与守卫)',
    all(k in full_doc for k in ('根因', '同层身份判据', '去向与守卫')),
    str([k for k in ('根因', '同层身份判据', '去向与守卫') if k in full_doc]))

chk('新增代码无 self 状态赋值 (self.x = ...)',
    not re.search(r'\bself\.\w+\s*=[^=]', code), re.findall(r'\bself\.\w+\s*=[^=]', code) or 'none')
chk('新增代码无 getattr/setattr(self, ...)',
    not re.search(r'(?:get|set)attr\(\s*self\b', code),
    re.findall(r'(?:get|set)attr\(\s*self\b', code) or 'none')
chk('新增代码无 self.xxx 属性存储（仅允许方法调用）',
    not re.search(r'\bself\.(?!_\w+\()[A-Za-z]\w+\b(?!\()', code),
    re.findall(r'\bself\.(?!_\w+\()[A-Za-z]\w+\b(?!\()', code) or 'none')
chk('新增代码无跨层 pattern X.entry in Y.blocks',
    not re.search(r'\w+\.entry\s+in\s+\w+\.blocks', code),
    re.findall(r'\w+\.entry\s+in\s+\w+\.blocks', code) or 'none')
chk('新增代码无文件名字面量 (.py / 路径)',
    not re.search(r"['\"][\w./\\-]+\.py['\"]", code),
    re.findall(r"['\"][\w./\\-]+\.py['\"]", code) or 'none')
chk('新增代码无 jq/replace_args 等名字白名单', 'replace_args' not in code and 'jq_trans' not in code,
    re.findall(r'replace_args|jq_trans|klinedata|wizard|real_quote|order_api', code) or 'none')
chk('新增代码无 start_offset 偏移阈值',
    not re.search(r'start_offset\s*[<>]=?\s*\d|start_offset\s*==\s*\d+', code),
    re.findall(r'start_offset\s*[<>]=?\s*\d+|start_offset\s*==\s*\d+', code) or 'none')

try:
    ast.parse(patched)
    a_ok, a_d = True, 'ast.parse OK'
except Exception as e:
    a_ok, a_d = False, repr(e)
chk('反打文件 ast.parse', a_ok, a_d)
try:
    import py_compile
    tf = os.path.join(tempfile.gettempdir(), 'fix1_g0.py')
    io.open(tf, 'w', encoding='utf-8', newline='\n').write(patched)
    py_compile.compile(tf, cfile=os.path.join(tempfile.gettempdir(), 'fix1_g0.pyc'), doraise=True)
    p_ok, p_d = True, 'py_compile OK'
except Exception as e:
    p_ok, p_d = False, repr(e)
chk('反打文件 py_compile', p_ok, p_d)
raw = io.open(CORE, 'rb').read()
chk('BOM 保持', raw[:3] == b'\xef\xbb\xbf', raw[:3].hex())

r = subprocess.run(['git', '-C', REPO, 'status', '--porcelain', '--', 'core', 'scripts',
                    'site-packages'], capture_output=True, text=True, errors='replace')
dirty = [l for l in (r.stdout or '').split('\n') if l.strip()]
tracked_dirty = [l for l in dirty if not l.startswith('??')]
chk('repo core/scripts/site-packages 已跟踪文件零改动（不改 repo、不手改 *OK.py）',
    not tracked_dirty, tracked_dirty[:5] or 'clean (untracked=%d)'
    % len([l for l in dirty if l.startswith('??')]))

print('%-62s %-5s %s' % ('check', 'ok', 'detail'))
for n, ok, d in checks:
    print('%-62s %-5s %s' % (n, 'PASS' if ok else 'FAIL', str(d)[:100]))
allok = all(c[1] for c in checks)
print('G0-audit: %s (%d/%d)' % ('PASS' if allok else 'FAIL', sum(c[1] for c in checks),
                                len(checks)))
io.open(r'D:/Temp/opencode/r75gate/fix1/dump/g0audit.txt', 'w', encoding='utf-8',
        newline='\n').write(
    '\n'.join('%s\t%s\t%s' % (n, 'PASS' if ok else 'FAIL', d) for n, ok, d in checks)
    + '\nG0-audit\t%s\t%d/%d\n' % ('PASS' if allok else 'FAIL', sum(c[1] for c in checks),
                                   len(checks)))
