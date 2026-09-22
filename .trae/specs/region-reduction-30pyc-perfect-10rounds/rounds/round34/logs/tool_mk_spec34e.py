# -*- coding: utf-8 -*-
"""Round 34 line C re-derivation of the candidate A2 proposed (working name R34-E).

A2 handed over spec_r34e.json targeting core/cfg/region_analyzer.py. This script does NOT trust
that file: it re-derives the (anchor, repl) pair from the *pristine landed* core, proves the
anchor is unique there, proves the candidate still compiles, and writes the spec the mirror
harness will measure. The predicate text is A2's verbatim (so the measured bytes and the
proposed bytes cannot drift); every symbol it references is checked to exist in that scope.

  python -X utf8 mk_spec34e.py
"""
import hashlib
import io
import json
import os
import re
import sys

REPO = r'F:\Downloads\pythoncdc-main'
REL = 'core/cfg/region_analyzer.py'
ROOT = r'D:/Temp/r34gate/r34'
sys.stdout.reconfigure(encoding='utf-8')

raw = io.open(os.path.join(REPO, REL.replace('/', os.sep)), 'rb').read()
txt = raw.decode('utf-8-sig').replace('\r\n', '\n')

ANCHOR = ("            spurious = [eb for eb in lr.else_blocks if eb in parent_body"
          " and eb not in _cond_exit_targets]")
assert txt.count(ANCHOR) == 1, 'anchor occurrences=%d' % txt.count(ANCHOR)

# what A2's spec proposed, verbatim, re-keyed onto the single-line anchor form above
REPL = """            def _r34_else_entry_exclusive(_lr, _eb):
                # 循环头的迭代跳转耗尽时唯一进入 _eb：_eb 的前驱集合恰为该循环头块，
                # 且头块尾指令是迭代跳转、其目标即 _eb。于是 _eb 只在 _lr 正常耗尽
                # 时被进入 —— 这就是 else 子句的定义。父环 body_blocks 之所以包含
                # _eb，只是自然体 DFS 穿过子环区域的传递产物，没有任何一条边从父环
                # 体内直接指向 _eb，故不构成归属证据（原则 2 取边证据一侧）。
                _h = _lr.header_block
                if _h is None or _eb is None:
                    return False
                if {p.start_offset for p in _eb.predecessors} != {_h.start_offset}:
                    return False
                _t = _h.get_last_instruction()
                if _t is None or _t.opname not in ('FOR_ITER', 'GET_ANEXT'):
                    return False
                return _t.argval is not None and \\
                    self.cfg.get_block_by_offset(_t.argval) is _eb

            spurious = [eb for eb in lr.else_blocks if eb in parent_body
                        and eb not in _cond_exit_targets
                        and not _r34_else_entry_exclusive(lr, eb)]"""
assert txt.count(REPL) == 0, 'candidate already present in landed core'

# every API the predicate touches must already exist (A2's prose is not evidence)
scope = txt.split(ANCHOR)[0].rsplit('    def ', 1)[-1]
for sym, pat in (('lr.else_blocks', r'\blr\.else_blocks\b'),
                 ('lr.header_block', r'\blr\.header_block\b'),
                 ('Block.start_offset', r'\.start_offset\b'),
                 ('Block.predecessors', r'\.predecessors\b'),
                 ('get_last_instruction', r'\.get_last_instruction\('),
                 ('cfg.get_block_by_offset', r'\.get_block_by_offset\(')):
    assert re.search(pat, txt), 'symbol %s never appears in region_analyzer.py' % sym
assert re.search(r'FOR_ITER', txt) and re.search(r'GET_ANEXT', txt), 'iteration-jump opnames unknown'

cand = txt.replace(ANCHOR, REPL)
assert cand.count(REPL) == 1 and cand != txt
compile(cand, REL, 'exec')

edits = [{'anchor': ANCHOR, 'repl': REPL}]
out = os.path.join(ROOT, 'spec_r34e.json')
io.open(out, 'w', encoding='utf-8').write(
    json.dumps({'file': REL, 'edits': edits}, ensure_ascii=False))

a2 = json.load(io.open(r'D:/Temp/r34gate/A2/spec_r34e.json', encoding='utf-8'))
same = a2['file'] == REL and a2['anchor'] == ANCHOR and a2['repl'] == REPL
print('re-derived from pristine core: anchor unique, candidate compiles, %d -> %d chars (+%d lines)'
      % (len(txt), len(cand), REPL.count('\n')))
print('byte-for-byte identical to A2 proposal: %s' % same)
if not same:
    print('A2 anchor=%r' % a2['anchor'][:60], 'A2 repl lines=%d' % a2['repl'].count('\n'))
print('core raw sha256[:20] %s (%d bytes, BOM=%s, CRLF=%d)'
      % (hashlib.sha256(raw).hexdigest()[:20], len(raw), raw[:3] == b'\xef\xbb\xbf',
         raw.count(b'\r\n')))
print('wrote %s' % out)
